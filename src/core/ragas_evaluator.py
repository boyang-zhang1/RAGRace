"""
Ragas evaluation wrapper for RAG systems.

Provides a clean interface to Ragas metrics for evaluating RAG provider responses.
Uses standard Ragas metrics: Faithfulness, FactualCorrectness, LLMContextRecall.
"""

import os
import time
from typing import List, Dict, Any
from dataclasses import dataclass

from ragas import evaluate, EvaluationDataset
from ragas.metrics import LLMContextRecall, Faithfulness, FactualCorrectness
from ragas.llms import llm_factory


@dataclass
class RAGEvaluationSample:
    """
    Sample for RAG evaluation.

    Maps to Ragas EvaluationDataset format:
    - user_input: The question
    - reference: Ground truth answer
    - retrieved_contexts: List of retrieved document chunks
    - response: RAG system's generated answer
    """
    user_input: str
    reference: str
    retrieved_contexts: List[str]
    response: str
    metadata: Dict[str, Any] = None


@dataclass
class EvaluationResult:
    """Results from Ragas evaluation."""
    scores: Dict[str, float]  # Metric name -> score
    raw_results: Any  # Raw Ragas result object
    sample_count: int


class RagasEvaluator:
    """
    Wrapper around Ragas evaluation library.

    Simplifies evaluation of RAG systems using standard metrics:
    - Faithfulness: Is the answer grounded in retrieved context?
    - FactualCorrectness: Does answer match ground truth?
    - LLMContextRecall: Was relevant context retrieved?
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize Ragas evaluator.

        Args:
            config: Optional config dict with:
                - model: LLM model name (default: gpt-4o-mini)
                - api_key_env: Environment variable for API key (default: OPENAI_API_KEY)
                - metrics: List of metric names to use (default: all)
        """
        config = config or {}

        # Get LLM configuration
        model = config.get('model', 'gpt-4o-mini')
        api_key_env = config.get('api_key_env', 'OPENAI_API_KEY')
        api_key = os.getenv(api_key_env)

        if not api_key:
            raise ValueError(f"API key not found in environment variable: {api_key_env}")

        # Initialize LLM for Ragas using modern factory
        self.evaluator_llm = llm_factory(model)

        # Initialize metrics
        metric_names = config.get('metrics', ['faithfulness', 'factual_correctness', 'context_recall'])
        self.metrics = self._init_metrics(metric_names, self.evaluator_llm)

    def _init_metrics(self, metric_names: List[str], llm: Any) -> List[Any]:
        """Initialize Ragas metrics from names with LLM set."""
        metric_map = {
            'faithfulness': Faithfulness(llm=llm),
            'factual_correctness': FactualCorrectness(llm=llm),
            'context_recall': LLMContextRecall(llm=llm),
        }

        metrics = []
        for name in metric_names:
            name_lower = name.lower()
            if name_lower in metric_map:
                metrics.append(metric_map[name_lower])
            else:
                available = ', '.join(metric_map.keys())
                raise ValueError(f"Unknown metric: {name}. Available: {available}")

        return metrics

    def evaluate_samples(
        self,
        samples: List[RAGEvaluationSample]
    ) -> EvaluationResult:
        """
        Evaluate RAG system responses using Ragas.

        Args:
            samples: List of evaluation samples with questions, contexts, responses, references

        Returns:
            EvaluationResult with averaged scores across all samples
        """
        if not samples:
            raise ValueError("No samples provided for evaluation")

        # Convert to Ragas format
        dataset_list = [
            {
                "user_input": sample.user_input,
                "reference": sample.reference,
                "retrieved_contexts": sample.retrieved_contexts,
                "response": sample.response,
            }
            for sample in samples
        ]

        # Create Ragas EvaluationDataset
        evaluation_dataset = EvaluationDataset.from_list(dataset_list)

        # Run evaluation with retry logic for rate limits
        max_retries = 5
        base_delay = 2.0
        result = None

        for attempt in range(max_retries):
            try:
                # Run evaluation (disable progress bar to avoid clutter in parallel execution)
                result = evaluate(
                    dataset=evaluation_dataset,
                    metrics=self.metrics,
                    llm=self.evaluator_llm,
                    show_progress=False
                )
                break  # Success - exit retry loop

            except Exception as e:
                error_msg = str(e)
                is_rate_limit = "rate_limit" in error_msg.lower() or "429" in error_msg

                if is_rate_limit and attempt < max_retries - 1:
                    # Exponential backoff with jitter
                    delay = base_delay * (2 ** attempt) + (time.time() % 1)
                    print(f"      ⚠️  Rate limit hit (attempt {attempt + 1}/{max_retries}), retrying in {delay:.1f}s...")
                    time.sleep(delay)
                else:
                    # Non-rate-limit error or final attempt - re-raise
                    if attempt == max_retries - 1:
                        print(f"      ❌ Failed after {max_retries} attempts: {error_msg}")
                    raise

        if result is None:
            raise RuntimeError("Evaluation failed - no result returned")

        # Extract scores from Ragas EvaluationResult
        # The Ragas evaluate() function returns an EvaluationResult with .scores dict
        # Convert to pandas and get mean scores
        result_df = result.to_pandas()

        # Get mean scores for each metric (excluding non-metric columns)
        metric_columns = [col for col in result_df.columns
                          if col not in ['user_input', 'reference', 'response', 'retrieved_contexts']]

        scores = {}
        for metric in metric_columns:
            if metric in result_df.columns:
                # Calculate mean score across all samples
                mean_score = result_df[metric].mean()
                scores[metric] = float(mean_score)

        return EvaluationResult(
            scores=scores,
            raw_results=result,
            sample_count=len(samples)
        )

    def evaluate_single_provider(
        self,
        questions: List[str],
        references: List[str],
        retrieved_contexts: List[List[str]],
        responses: List[str],
    ) -> EvaluationResult:
        """
        Convenience method to evaluate a single RAG provider.

        Args:
            questions: List of questions asked
            references: List of ground truth answers
            retrieved_contexts: List of context lists (one per question)
            responses: List of RAG system responses

        Returns:
            EvaluationResult with averaged scores
        """
        if not (len(questions) == len(references) == len(retrieved_contexts) == len(responses)):
            raise ValueError("All input lists must have the same length")

        samples = [
            RAGEvaluationSample(
                user_input=q,
                reference=ref,
                retrieved_contexts=ctx,
                response=resp
            )
            for q, ref, ctx, resp in zip(questions, references, retrieved_contexts, responses)
        ]

        return self.evaluate_samples(samples)
