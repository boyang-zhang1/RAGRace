"""
Provider executor - runs one RAG provider on one paper.

This module executes in a thread and handles:
- Document ingestion
- Question querying
- Response evaluation
- Error handling
"""

import time
from datetime import datetime
from typing import List

from src.adapters.base import BaseAdapter, Document, RAGResponse
from src.core.schemas import PaperData, QuestionData, QuestionResult, ProviderResult
from src.core.ragas_evaluator import RagasEvaluator, RAGEvaluationSample


class ProviderExecutor:
    """Executes a single provider on a single paper."""

    def __init__(self, evaluator: RagasEvaluator):
        """
        Initialize executor.

        Args:
            evaluator: Ragas evaluator instance (shared across providers)
        """
        self.evaluator = evaluator

    def execute(
        self,
        provider_name: str,
        adapter: BaseAdapter,
        paper: PaperData,
        questions: List[QuestionData]
    ) -> ProviderResult:
        """
        Execute complete provider workflow on one paper.

        Workflow:
        1. Ingest paper PDF
        2. Query all questions
        3. Evaluate responses with Ragas
        4. Aggregate scores
        5. Return structured result

        Thread-safe: Each provider gets own adapter instance.
        Error handling: Catches all exceptions and returns error status.

        Args:
            provider_name: Name of provider (for logging)
            adapter: Initialized adapter instance
            paper: Paper data with PDF path
            questions: List of questions to ask

        Returns:
            ProviderResult with status, results, or error
        """
        timestamp_start = datetime.now().isoformat()
        start_time = time.time()

        result = ProviderResult(
            provider=provider_name,
            paper_id=paper.paper_id,
            status="pending",
            timestamp_start=timestamp_start
        )

        try:
            # Step 1: Ingest paper PDF
            doc = Document(
                id=paper.paper_id,
                content="",  # File-based providers use metadata.file_path
                metadata={
                    'file_path': str(paper.pdf_path),
                    'title': paper.paper_title
                }
            )

            index_id = adapter.ingest_documents([doc])
            result.index_id = index_id

            # Step 2: Query all questions
            question_results = []
            ragas_samples = []

            for question_data in questions:
                # Query provider
                response: RAGResponse = adapter.query(
                    question=question_data.question,
                    index_id=index_id
                )

                # Store question result
                question_result = QuestionResult(
                    question_id=question_data.question_id,
                    question=question_data.question,
                    ground_truth=question_data.ground_truth,
                    response_answer=response.answer,
                    response_context=response.context,
                    response_latency_ms=response.latency_ms,
                    response_metadata=response.metadata,
                    evaluation_scores={}  # Filled after Ragas eval
                )
                question_results.append(question_result)

                # Prepare for Ragas evaluation
                ragas_sample = RAGEvaluationSample(
                    user_input=question_data.question,
                    reference=question_data.ground_truth,
                    retrieved_contexts=response.context,
                    response=response.answer,
                    metadata={'provider': provider_name}
                )
                ragas_samples.append(ragas_sample)

            # Step 3: Evaluate with Ragas (batch evaluation with retry)
            print(f"      🔍 Evaluating {len(ragas_samples)} responses with Ragas...")
            max_retries = 3
            eval_result = None
            last_error = None

            for attempt in range(max_retries):
                try:
                    eval_result = self.evaluator.evaluate_samples(ragas_samples)

                    # Check for NaN values in scores
                    has_nan = any(
                        score != score  # NaN != NaN is True
                        for score in eval_result.scores.values()
                    )

                    if has_nan:
                        print(f"      ⚠️  NaN detected in evaluation scores (attempt {attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            time.sleep(2)  # Brief delay before retry
                            continue
                        else:
                            # Last attempt - clean NaN values
                            cleaned_scores = {}
                            for metric, score in eval_result.scores.items():
                                if score != score:  # NaN check
                                    cleaned_scores[metric] = 0.0
                                    print(f"      ⚠️  Replacing NaN with 0.0 for {metric}")
                                else:
                                    cleaned_scores[metric] = score
                            eval_result.scores = cleaned_scores

                    # Success - break retry loop
                    break

                except Exception as e:
                    last_error = e
                    print(f"      ⚠️  Evaluation failed (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2)  # Brief delay before retry
                    else:
                        raise

            if eval_result is None:
                raise RuntimeError(f"Evaluation failed after {max_retries} attempts: {last_error}")

            # Step 4: Extract per-question scores
            # Ragas returns averaged scores - we use same scores for all questions
            # (Ragas doesn't provide per-sample breakdown in current API)
            for question_result in question_results:
                question_result.evaluation_scores = eval_result.scores.copy()

            # Step 5: Aggregate scores (already done by Ragas)
            result.questions = question_results
            result.aggregated_scores = eval_result.scores.copy()
            result.status = "success"

        except Exception as e:
            # Error handling: log error and return error status
            result.status = "error"
            result.error = f"{type(e).__name__}: {str(e)}"

        finally:
            # Record timing
            end_time = time.time()
            result.duration_seconds = end_time - start_time
            result.timestamp_end = datetime.now().isoformat()

            # Add duration as a metric (lower is better, unlike quality metrics)
            if result.status == "success" and result.aggregated_scores:
                result.aggregated_scores['duration_seconds'] = result.duration_seconds

        return result
