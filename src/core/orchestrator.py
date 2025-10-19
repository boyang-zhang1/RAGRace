"""
Orchestrator - main entry point for RAGRace benchmark.

Coordinates:
- Configuration loading
- Dataset loading
- Adapter initialization
- Document processing
- Result aggregation
"""

import time
import yaml
import threading
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple

from src.datasets.loader import DatasetLoader
from src.core.schemas import DocumentData, QuestionData, RunSummary, ProviderResult, DocumentResult
from src.core.adapter_factory import AdapterFactory
from src.core.ragas_evaluator import RagasEvaluator
from src.core.document_processor import DocumentProcessor
from src.core.provider_executor import ProviderExecutor
from src.core.result_saver import ResultSaver


class Orchestrator:
    """Main orchestrator for RAGRace benchmark."""

    def __init__(self, config_path: str):
        """
        Initialize orchestrator.

        Args:
            config_path: Path to benchmark config file (e.g., config/benchmark_qasper.yaml)
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

    def _create_task_combinations(
        self,
        docs: List[DocumentData],
        questions_by_doc: Dict[str, List[QuestionData]],
        adapters: Dict
    ) -> List[Tuple]:
        """
        Generate all (provider, doc, questions) task combinations.

        Args:
            docs: List of documents
            questions_by_doc: Questions grouped by document ID
            adapters: Dict of initialized adapters {name: adapter}

        Returns:
            List of (provider_name, adapter, doc, questions) tuples
        """
        tasks = []
        for doc in docs:
            questions = questions_by_doc[doc.doc_id]
            for provider_name, adapter in adapters.items():
                tasks.append((provider_name, adapter, doc, questions))
        return tasks

    def _should_skip_task(self, provider_name: str, doc_id: str) -> bool:
        """
        Check if (provider, doc) task should be skipped (resume capability).

        Args:
            provider_name: Provider name
            doc_id: Document ID

        Returns:
            True if task already completed, False otherwise
        """
        if not self.output_config.get('resume_enabled', False):
            return False

        # Check if provider result file exists
        provider_result_path = self.result_saver.docs_dir / doc_id / f"{provider_name}.json"
        return provider_result_path.exists()

    def run_benchmark(self) -> RunSummary:
        """
        Execute complete benchmark with (provider, document) parallelization.

        New Workflow (optimized for parallelism):
        1. Load dataset (docs + questions)
        2. Initialize all adapters
        3. Create (provider, doc) task combinations
        4. Execute all tasks in parallel with:
           - Per-provider rate limiting (semaphores)
           - RAGAS evaluation queue (semaphore)
        5. Save results incrementally as tasks complete
        6. Aggregate results per document
        7. Generate run summary

        Returns:
            RunSummary with all results
        """
        timestamp_start = datetime.now().isoformat()
        start_time = time.time()

        print("\n" + "="*80)
        print("🏁 RAGRACE BENCHMARK (Parallel Execution)")
        print("="*80)
        print(f"Config: {self.config_path}")
        print(f"Dataset: {self.dataset_config['name']}")
        print(f"Providers: {', '.join(self.provider_names)}")
        print(f"Results: {self.result_saver.run_dir}")
        print("="*80)

        # Step 1: Load dataset
        print(f"\n📥 Loading dataset...")
        docs, questions_by_doc = self._load_dataset()

        total_questions = sum(len(qs) for qs in questions_by_doc.values())
        print(f"   ✓ Loaded {len(docs)} docs, {total_questions} questions")

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

        # Step 4: Create semaphores for rate limiting
        # Per-provider semaphores (limit concurrent tasks per provider)
        max_per_provider = self.execution_config.get('max_per_provider_workers', 3)
        provider_semaphores = {
            provider_name: threading.Semaphore(max_per_provider)
            for provider_name in self.provider_names
        }

        # RAGAS evaluation semaphore (limit concurrent evaluations)
        max_ragas = self.execution_config.get('max_ragas_workers', 5)
        ragas_semaphore = threading.Semaphore(max_ragas)

        print(f"\n🔧 Parallelization settings:")
        print(f"   Max total workers: {self.execution_config.get('max_total_workers', 9)}")
        print(f"   Max per-provider workers: {max_per_provider}")
        print(f"   Max RAGAS workers: {max_ragas}")

        # Step 5: Generate task combinations
        print(f"\n🔄 Generating task combinations...")
        tasks = self._create_task_combinations(docs, questions_by_doc, adapters)

        # Filter tasks based on resume capability
        tasks_to_run = []
        tasks_skipped = 0
        for provider_name, adapter, doc, questions in tasks:
            if self._should_skip_task(provider_name, doc.doc_id):
                tasks_skipped += 1
                print(f"   ⏭️  Skipping {provider_name} + {doc.doc_id} (already completed)")
            else:
                tasks_to_run.append((provider_name, adapter, doc, questions))

        total_tasks = len(tasks)
        tasks_to_execute = len(tasks_to_run)

        print(f"   ✓ Total task combinations: {total_tasks}")
        print(f"   ✓ Tasks to execute: {tasks_to_execute} ({total_tasks - tasks_to_execute} skipped)")
        print(f"   ✓ Expected parallelism: {len(docs)} docs × {len(self.provider_names)} providers")

        # Step 6: Execute tasks in parallel
        print(f"\n🚀 Executing {tasks_to_execute} tasks in parallel...")
        print(f"{'='*80}")

        # Create provider executor
        provider_executor = ProviderExecutor(evaluator=evaluator)

        # Track results per document
        doc_results_map = defaultdict(dict)  # {doc_id: {provider_name: ProviderResult}}

        # Execute tasks with thread pool
        max_total_workers = self.execution_config.get('max_total_workers', 9)
        with ThreadPoolExecutor(max_workers=max_total_workers) as pool:
            # Submit all tasks
            future_to_task = {}
            for provider_name, adapter, doc, questions in tasks_to_run:
                future = pool.submit(
                    provider_executor.execute,
                    provider_name=provider_name,
                    adapter=adapter,
                    doc=doc,
                    questions=questions,
                    provider_semaphore=provider_semaphores[provider_name],
                    ragas_semaphore=ragas_semaphore
                )
                future_to_task[future] = (provider_name, doc.doc_id, doc.doc_title)
                print(f"   ✓ Submitted: {provider_name} + {doc.doc_id[:40]}")

            # Collect results as they complete
            print(f"\n⏳ Waiting for {tasks_to_execute} tasks to complete...")
            print(f"{'='*80}")

            completed_count = 0
            for future in as_completed(future_to_task):
                provider_name, doc_id, doc_title = future_to_task[future]

                try:
                    result: ProviderResult = future.result()

                    # Store result
                    doc_results_map[doc_id][provider_name] = result
                    completed_count += 1

                    # Log completion
                    status_icon = "✅" if result.status == "success" else "❌"
                    progress = f"[{completed_count}/{tasks_to_execute}]"
                    print(f"\n{status_icon} {progress} {provider_name} + {doc_id[:40]}")
                    print(f"   Duration: {result.duration_seconds:.1f}s")

                    if result.status == "success":
                        scores_str = ", ".join([f"{k}={v:.3f}" for k, v in result.aggregated_scores.items() if k != 'duration_seconds'])
                        print(f"   Scores: {scores_str}")
                    else:
                        print(f"   Error: {result.error}")

                    # Save provider result incrementally
                    self.result_saver.save_provider_result(result)

                except Exception as e:
                    # Handle thread execution errors
                    print(f"\n❌ [{completed_count + 1}/{tasks_to_execute}] {provider_name} + {doc_id} thread failed: {e}")
                    completed_count += 1

        # Step 7: Aggregate results per document
        print(f"\n📊 Aggregating results per document...")
        doc_results = []

        for doc in docs:
            if doc.doc_id in doc_results_map:
                provider_results = doc_results_map[doc.doc_id]

                # Create DocumentResult
                doc_result = DocumentResult(
                    doc_id=doc.doc_id,
                    doc_title=doc.doc_title,
                    num_questions=len(questions_by_doc[doc.doc_id]),
                    timestamp=datetime.now().isoformat(),
                    providers=provider_results
                )

                # Determine winner (aggregate scores)
                doc_result.winner = self._aggregate_provider_scores(provider_results)

                # Save aggregated document result
                self.result_saver.save_document_aggregated(doc_result)

                doc_results.append(doc_result)

                print(f"   ✓ Aggregated results for {doc.doc_id}")
            else:
                print(f"   ⚠️  No results for {doc.doc_id} (all tasks skipped or failed)")

        print(f"   ✓ Aggregated {len(doc_results)} documents")

        # Step 5: Generate run summary
        print(f"\n📊 Generating run summary...")
        end_time = time.time()
        duration = end_time - start_time

        # Determine overall winner (most metrics won across all docs)
        overall_winner = self._determine_overall_winner(doc_results)

        summary = RunSummary(
            run_id=self.result_saver.run_id,
            config=self.config,
            num_docs=len(docs),
            num_questions_total=total_questions,
            providers=self.provider_names,
            results=doc_results,
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

    def _load_dataset(self) -> Tuple[List[DocumentData], Dict[str, List[QuestionData]]]:
        """
        Load dataset generically and group questions by document.

        Supports any dataset type via config-driven DatasetLoader routing.
        Groups questions by document:
        - PDF-based datasets (Qasper): group by doc_id (one PDF per document)
        - Text-based datasets (PolicyQA): group by unique context (one paragraph per document)

        Returns:
            (documents, questions_by_document)
            - documents: List[DocumentData] (generic document data)
            - questions_by_document: Dict[document_id, List[QuestionData]]
        """
        dataset_name = self.dataset_config['name']

        # Generic dataset loading via DatasetLoader
        # The loader routes to the correct preprocessor based on dataset name
        loader = DatasetLoader(dataset_type=dataset_name)

        # Build kwargs from config (filter out None values)
        load_kwargs = {
            k: v for k, v in self.dataset_config.items()
            if k not in ['name'] and v is not None
        }

        dataset = loader.load(file_path=None, **load_kwargs)

        # Generic grouping: determine strategy based on sample metadata
        # If samples have 'doc_id' and 'pdf_path' → PDF-based (group by doc_id)
        # Otherwise → text-based (group by unique context)

        if dataset.samples and 'pdf_path' in dataset.samples[0].metadata:
            # PDF-based dataset (Qasper)
            documents, questions_by_doc = self._group_by_pdf(dataset)
        else:
            # Text-based dataset (PolicyQA, SQuAD)
            documents, questions_by_doc = self._group_by_context(dataset)

        return documents, questions_by_doc

    def _group_by_pdf(self, dataset) -> Tuple[List[DocumentData], Dict[str, List[QuestionData]]]:
        """Group PDF-based dataset samples by doc_id."""
        from collections import defaultdict
        import hashlib

        docs_dict = defaultdict(list)

        for sample in dataset.samples:
            doc_id = sample.metadata['doc_id']
            docs_dict[doc_id].append(sample)

        # Limit questions per doc if configured
        max_questions = self.dataset_config.get('max_questions_per_doc') or \
                       self.dataset_config.get('max_questions_per_document')

        docs = []
        questions_by_doc = {}

        for doc_id, samples in docs_dict.items():
            # Limit questions
            if max_questions:
                samples = samples[:max_questions]

            # Create DocumentData
            first_sample = samples[0]
            doc = DocumentData(
                doc_id=doc_id,
                doc_title=first_sample.metadata.get('doc_title', doc_id),
                pdf_path=Path(first_sample.metadata['pdf_path']),
                pdf_size_bytes=Path(first_sample.metadata['pdf_path']).stat().st_size,
                metadata=first_sample.metadata
            )
            docs.append(doc)

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
            questions_by_doc[doc_id] = questions

        return docs, questions_by_doc

    def _group_by_context(self, dataset) -> Tuple[List[DocumentData], Dict[str, List[QuestionData]]]:
        """Group text-based dataset samples by unique context."""
        from collections import defaultdict
        import hashlib

        # Group by context (each unique context = one document)
        context_dict = defaultdict(list)
        context_to_id = {}

        for sample in dataset.samples:
            # Create unique ID for this context
            context_hash = hashlib.md5(sample.context.encode()).hexdigest()[:16]

            # For PolicyQA: use website_title as prefix for readability
            website_title = sample.metadata.get('website_title', 'doc')
            doc_id = f"{website_title}_{context_hash}"

            context_dict[doc_id].append(sample)
            context_to_id[doc_id] = sample.context

        # Limit questions per document if configured
        max_questions = self.dataset_config.get('max_questions_per_doc') or \
                       self.dataset_config.get('max_questions_per_document') or \
                       self.dataset_config.get('max_samples')

        documents = []
        questions_by_doc = {}

        for doc_id, samples in context_dict.items():
            # Limit questions
            if max_questions:
                samples = samples[:max_questions]

            # Create DocumentData (repurposed for text documents)
            first_sample = samples[0]
            context_text = first_sample.context

            # Store text content in metadata since no PDF exists
            document = DocumentData(
                doc_id=doc_id,
                doc_title=first_sample.metadata.get('website_title', doc_id),
                pdf_path=None,  # No PDF for text-based datasets
                pdf_size_bytes=len(context_text.encode()),  # Text size in bytes
                metadata={
                    **first_sample.metadata,
                    'content': context_text,  # Store text content here
                    'document_type': 'text'
                }
            )
            documents.append(document)

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
            questions_by_doc[doc_id] = questions

        return documents, questions_by_doc

    def _aggregate_provider_scores(self, provider_results: Dict[str, ProviderResult]) -> Dict:
        """
        Aggregate scores from provider results for a single document.

        This method extracts scores from each provider and creates
        a summary structure compatible with the existing result format.

        Args:
            provider_results: Dict of {provider_name: ProviderResult}

        Returns:
            Dict with {"provider_scores": {provider: scores}}
        """
        provider_scores = {}

        for provider_name, result in provider_results.items():
            if result.status == "success":
                provider_scores[provider_name] = result.aggregated_scores

        return {"provider_scores": provider_scores}

    def _determine_overall_winner(self, doc_results: List) -> Dict:
        """
        Calculate average metric scores across all docs (no ranking).

        Returns:
            Dict with average scores for each provider
        """
        from collections import defaultdict

        # Collect scores for each provider across all docs
        provider_metric_scores = defaultdict(lambda: defaultdict(list))

        for doc_result in doc_results:
            provider_scores = doc_result.winner.get("provider_scores", {})
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
        print(f"Documents processed: {summary.num_docs}")
        print(f"Total questions: {summary.num_questions_total}")
        print(f"Duration: {summary.duration_seconds:.1f}s")

        # Print average scores
        provider_avg_scores = summary.overall_winner.get("provider_avg_scores", {})
        if provider_avg_scores:
            print(f"\n📊 Overall Average Scores (across {summary.num_docs} docs):")
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
