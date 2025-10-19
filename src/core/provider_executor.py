"""
Provider executor - runs one RAG provider on one document.

This module executes in a thread and handles:
- Document ingestion
- Question querying
- Response evaluation
- Error handling
- Rate limiting via semaphores
"""

import time
import threading
from datetime import datetime
from typing import List, Optional

from src.adapters.base import BaseAdapter, Document, RAGResponse
from src.core.schemas import DocumentData, QuestionData, QuestionResult, ProviderResult
from src.core.ragas_evaluator import RagasEvaluator, RAGEvaluationSample


class ProviderExecutor:
    """Executes a single provider on a single document."""

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
        doc: DocumentData,
        questions: List[QuestionData],
        provider_semaphore: Optional[threading.Semaphore] = None,
        ragas_semaphore: Optional[threading.Semaphore] = None
    ) -> ProviderResult:
        """
        Execute complete provider workflow on one document with rate limiting.

        Workflow:
        1. Acquire provider semaphore (rate limit per provider)
        2. Ingest document (PDF or text)
        3. Query all questions
        4. Acquire RAGAS semaphore (rate limit evaluations)
        5. Evaluate responses with Ragas
        6. Release semaphores
        7. Aggregate scores
        8. Return structured result

        Thread-safe: Each provider gets own adapter instance.
        Error handling: Catches all exceptions and returns error status.
        Rate limiting: Uses semaphores to limit concurrent operations.

        Args:
            provider_name: Name of provider (for logging)
            adapter: Initialized adapter instance
            doc: Document data (PDF path or text content)
            questions: List of questions to ask
            provider_semaphore: Optional semaphore for per-provider rate limiting
            ragas_semaphore: Optional semaphore for RAGAS evaluation rate limiting

        Returns:
            ProviderResult with status, results, or error
        """
        timestamp_start = datetime.now().isoformat()
        start_time = time.time()

        result = ProviderResult(
            provider=provider_name,
            doc_id=doc.doc_id,
            status="pending",
            timestamp_start=timestamp_start
        )

        # Acquire provider semaphore (rate limiting)
        if provider_semaphore:
            print(f"      ⏳ {provider_name} waiting for provider slot...")
            provider_semaphore.acquire()
            print(f"      ✓ {provider_name} acquired provider slot")

        try:
            # Step 1: Ingest document (PDF or text)
            # For PDF-based datasets (Qasper): use file_path
            # For text-based datasets (PolicyQA): use content
            if doc.pdf_path is not None:
                # PDF-based document
                document = Document(
                    id=doc.doc_id,
                    content="",  # File-based providers use metadata.file_path
                    metadata={
                        'file_path': str(doc.pdf_path),
                        'title': doc.doc_title
                    }
                )
            else:
                # Text-based document
                document = Document(
                    id=doc.doc_id,
                    content=doc.metadata.get('content', ''),
                    metadata={
                        'title': doc.doc_title,
                        'document_type': 'text'
                    }
                )

            index_id = adapter.ingest_documents([document])
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
            # Acquire RAGAS semaphore (rate limiting for OpenAI API)
            if ragas_semaphore:
                print(f"      ⏳ {provider_name} waiting for RAGAS evaluation slot...")
                ragas_semaphore.acquire()
                print(f"      ✓ {provider_name} acquired RAGAS slot")

            try:
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

            finally:
                # Release RAGAS semaphore
                if ragas_semaphore:
                    ragas_semaphore.release()
                    print(f"      ✓ {provider_name} released RAGAS slot")

        except Exception as e:
            # Error handling: log error and return error status
            result.status = "error"
            result.error = f"{type(e).__name__}: {str(e)}"

        finally:
            # Release provider semaphore
            if provider_semaphore:
                provider_semaphore.release()
                print(f"      ✓ {provider_name} released provider slot")

            # Record timing
            end_time = time.time()
            result.duration_seconds = end_time - start_time
            result.timestamp_end = datetime.now().isoformat()

            # Add duration as a metric (lower is better, unlike quality metrics)
            if result.status == "success" and result.aggregated_scores:
                result.aggregated_scores['duration_seconds'] = result.duration_seconds

        return result
