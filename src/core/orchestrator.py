"""
Orchestrator - main entry point for RAGRace benchmark.

Coordinates:
- Configuration loading
- Dataset loading
- Adapter initialization
- Paper processing
- Result aggregation
"""

import time
import yaml
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple

from src.datasets.loader import DatasetLoader
from src.core.schemas import PaperData, QuestionData, RunSummary
from src.core.adapter_factory import AdapterFactory
from src.core.ragas_evaluator import RagasEvaluator
from src.core.paper_processor import PaperProcessor
from src.core.result_saver import ResultSaver


class Orchestrator:
    """Main orchestrator for RAGRace benchmark."""

    def __init__(self, config_path: str):
        """
        Initialize orchestrator.

        Args:
            config_path: Path to benchmark.yaml config file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()

        # Extract config sections
        self.benchmark_config = self.config['benchmark']
        self.dataset_config = self.benchmark_config['dataset']
        self.execution_config = self.benchmark_config['execution']
        self.provider_names = self.benchmark_config['providers']
        self.provider_configs = self.benchmark_config['provider_configs']
        self.eval_config = self.benchmark_config['evaluation']
        self.output_config = self.benchmark_config['output']

        # Initialize result saver
        self.result_saver = ResultSaver(
            output_dir=Path(self.output_config['results_dir'])
        )

        # Save config snapshot
        self.result_saver.save_config(self.config)

    def _load_config(self) -> Dict:
        """Load configuration from YAML file."""
        with open(self.config_path) as f:
            return yaml.safe_load(f)

    def run_benchmark(self) -> RunSummary:
        """
        Execute complete benchmark.

        Workflow:
        1. Load dataset (papers + questions)
        2. Initialize all adapters
        3. For each paper:
           - PaperProcessor.process_paper() → parallel providers
           - Save results incrementally
        4. Generate run summary
        5. Return results

        Returns:
            RunSummary with all results
        """
        timestamp_start = datetime.now().isoformat()
        start_time = time.time()

        print("\n" + "="*80)
        print("🏁 RAGRACE BENCHMARK")
        print("="*80)
        print(f"Config: {self.config_path}")
        print(f"Dataset: {self.dataset_config['name']}")
        print(f"Providers: {', '.join(self.provider_names)}")
        print(f"Results: {self.result_saver.run_dir}")
        print("="*80)

        # Step 1: Load dataset
        print(f"\n📥 Loading dataset...")
        papers, questions_by_paper = self._load_dataset()

        total_questions = sum(len(qs) for qs in questions_by_paper.values())
        print(f"   ✓ Loaded {len(papers)} papers, {total_questions} questions")

        # Step 2: Initialize adapters
        print(f"\n📦 Initializing {len(self.provider_names)} providers...")
        adapters = AdapterFactory.create_all_adapters(
            provider_names=self.provider_names,
            provider_configs=self.provider_configs
        )
        print(f"   ✓ All providers initialized and healthy")

        # Step 3: Initialize evaluator
        print(f"\n📊 Initializing Ragas evaluator...")
        evaluator = RagasEvaluator(config=self.eval_config)
        print(f"   ✓ Ragas evaluator ready")

        # Step 4: Process each paper
        print(f"\n🔄 Processing papers...")
        paper_processor = PaperProcessor(
            evaluator=evaluator,
            max_workers=self.execution_config['max_provider_workers']
        )

        paper_results = []

        for i, paper in enumerate(papers, 1):
            print(f"\n{'='*80}")
            print(f"Paper {i}/{len(papers)}: {paper.paper_id}")
            print(f"{'='*80}")

            # Check if already completed (resume capability)
            if (self.output_config.get('resume_enabled', False) and
                self.result_saver.paper_completed(paper.paper_id)):
                print(f"⏭️  Skipping (already completed)")
                continue

            # Get questions for this paper
            questions = questions_by_paper[paper.paper_id]

            # Process paper with all providers (parallel)
            paper_result = paper_processor.process_paper(
                paper=paper,
                questions=questions,
                adapters=adapters,
                on_provider_complete=lambda result: self.result_saver.save_provider_result(result)
            )

            # Save aggregated paper result
            self.result_saver.save_paper_aggregated(paper_result)

            paper_results.append(paper_result)

        # Step 5: Generate run summary
        print(f"\n📊 Generating run summary...")
        end_time = time.time()
        duration = end_time - start_time

        # Determine overall winner (most metrics won across all papers)
        overall_winner = self._determine_overall_winner(paper_results)

        summary = RunSummary(
            run_id=self.result_saver.run_id,
            config=self.config,
            num_papers=len(papers),
            num_questions_total=total_questions,
            providers=self.provider_names,
            results=paper_results,
            overall_winner=overall_winner,
            duration_seconds=duration,
            timestamp_start=timestamp_start,
            timestamp_end=datetime.now().isoformat()
        )

        # Save summary
        self.result_saver.save_run_summary(summary)

        # Print final results
        self._print_summary(summary)

        return summary

    def _load_dataset(self) -> Tuple[List[PaperData], Dict[str, List[QuestionData]]]:
        """
        Load dataset and group questions by paper.

        Returns:
            (papers, questions_by_paper)
            - papers: List[PaperData]
            - questions_by_paper: Dict[paper_id, List[QuestionData]]
        """
        dataset_name = self.dataset_config['name']

        if dataset_name == 'qasper':
            dataset = DatasetLoader.load_qasper(
                split=self.dataset_config.get('split', 'train'),
                max_papers=self.dataset_config.get('max_papers'),
                filter_unanswerable=self.dataset_config.get('filter_unanswerable', True)
            )
        else:
            raise ValueError(f"Unsupported dataset: {dataset_name}")

        # Group samples by paper
        papers_dict = defaultdict(list)

        for sample in dataset.samples:
            paper_id = sample.metadata['paper_id']
            papers_dict[paper_id].append(sample)

        # Limit questions per paper if configured
        max_questions = self.dataset_config.get('max_questions_per_paper')

        # Convert to PaperData and QuestionData
        papers = []
        questions_by_paper = {}

        for paper_id, samples in papers_dict.items():
            # Limit questions
            if max_questions:
                samples = samples[:max_questions]

            # Create PaperData
            first_sample = samples[0]
            paper = PaperData(
                paper_id=paper_id,
                paper_title=first_sample.metadata['paper_title'],
                pdf_path=Path(first_sample.metadata['pdf_path']),
                pdf_size_bytes=Path(first_sample.metadata['pdf_path']).stat().st_size,
                metadata=first_sample.metadata
            )
            papers.append(paper)

            # Create QuestionData list
            questions = [
                QuestionData(
                    question_id=sample.metadata.get('question_id', f"q{i}"),
                    question=sample.question,
                    ground_truth=sample.ground_truth,
                    metadata=sample.metadata
                )
                for i, sample in enumerate(samples)
            ]
            questions_by_paper[paper_id] = questions

        return papers, questions_by_paper

    def _determine_overall_winner(self, paper_results: List) -> Dict:
        """
        Calculate average metric scores across all papers (no ranking).

        Returns:
            Dict with average scores for each provider
        """
        from collections import defaultdict

        # Collect scores for each provider across all papers
        provider_metric_scores = defaultdict(lambda: defaultdict(list))

        for paper_result in paper_results:
            provider_scores = paper_result.winner.get("provider_scores", {})
            for provider, scores in provider_scores.items():
                for metric, score in scores.items():
                    provider_metric_scores[provider][metric].append(score)

        if not provider_metric_scores:
            return {"provider_avg_scores": {}}

        # Calculate average for each metric for each provider
        provider_avg_scores = {}
        for provider, metric_scores in provider_metric_scores.items():
            avg_scores = {}
            for metric, scores in metric_scores.items():
                avg_scores[metric] = sum(scores) / len(scores)
            provider_avg_scores[provider] = avg_scores

        return {"provider_avg_scores": provider_avg_scores}

    def _print_summary(self, summary: RunSummary):
        """Print final summary."""
        print(f"\n{'='*80}")
        print(f"🏆 BENCHMARK COMPLETE")
        print(f"{'='*80}")
        print(f"Papers processed: {summary.num_papers}")
        print(f"Total questions: {summary.num_questions_total}")
        print(f"Duration: {summary.duration_seconds:.1f}s")

        # Print average scores
        provider_avg_scores = summary.overall_winner.get("provider_avg_scores", {})
        if provider_avg_scores:
            print(f"\n📊 Overall Average Scores (across {summary.num_papers} papers):")
            for provider in sorted(provider_avg_scores.keys()):
                scores = provider_avg_scores[provider]

                # Format scores nicely
                formatted_scores = []
                for k, v in sorted(scores.items()):
                    if k == 'duration_seconds':
                        formatted_scores.append(f"{k}={v:.1f}s")
                    else:
                        formatted_scores.append(f"{k}={v:.3f}")
                scores_str = ", ".join(formatted_scores)

                print(f"   {provider}: {scores_str}")

        print(f"\nResults: {self.result_saver.run_dir}")
        print(f"{'='*80}\n")
