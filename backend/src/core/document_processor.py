"""
Document processor - orchestrates parallel provider execution.

DEPRECATED: This class is kept for backward compatibility.
The new execution model in Orchestrator.run_benchmark() directly
manages (provider, document) task combinations with better parallelism.

This module (legacy):
- Creates thread pool for parallel execution
- Submits ProviderExecutor tasks
- Collects results as they complete
- Aggregates scores and determines winner

For new code, use Orchestrator directly instead of DocumentProcessor.
"""

from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Callable, Optional, Any

from src.adapters.base import BaseAdapter
from src.core.schemas import DocumentData, QuestionData, ProviderResult, DocumentResult
from src.core.ragas_evaluator import RagasEvaluator
from src.core.provider_executor import ProviderExecutor


class DocumentProcessor:
    """
    DEPRECATED: Processes a single document with multiple providers in parallel.

    This class is maintained for backward compatibility only.
    New code should use Orchestrator.run_benchmark() directly.
    """

    def __init__(self, evaluator: RagasEvaluator, max_workers: int = 3):
        """
        Initialize document processor.

        DEPRECATED: Use Orchestrator.run_benchmark() for new code.

        Args:
            evaluator: Ragas evaluator (shared across all providers)
            max_workers: Max concurrent provider threads (default: 3)
        """
        self.evaluator = evaluator
        self.max_workers = max_workers
        self.executor_factory = ProviderExecutor

    def process_document(
        self,
        doc: DocumentData,
        questions: List[QuestionData],
        adapters: Dict[str, BaseAdapter],
        on_provider_complete: Optional[Callable[[ProviderResult], None]] = None
    ) -> DocumentResult:
        """
        Execute all providers on this document in parallel.

        Workflow:
        1. Create thread pool (max_workers = num providers)
        2. Submit ProviderExecutor.execute() for each provider
        3. Collect results via as_completed() (save incrementally)
        4. Aggregate scores and determine winner
        5. Return complete document result

        Args:
            doc: Document data with content (PDF path or text)
            questions: Questions to ask all providers
            adapters: Dict of initialized adapters {name: adapter}
            on_provider_complete: Optional callback when each provider finishes

        Returns:
            DocumentResult with all provider results and winner
        """
        print(f"\n{'='*80}")
        print(f"📄 Processing document: {doc.doc_id}")
        print(f"   Title: {doc.doc_title[:70]}...")
        print(f"   Questions: {len(questions)}")
        print(f"   Providers: {list(adapters.keys())}")
        print(f"{'='*80}")

        # Initialize result
        doc_result = DocumentResult(
            doc_id=doc.doc_id,
            doc_title=doc.doc_title,
            num_questions=len(questions),
            timestamp=datetime.now().isoformat()
        )

        # Create provider executor
        executor = self.executor_factory(evaluator=self.evaluator)

        # Submit all providers to thread pool
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            # Map: future → provider name
            future_to_provider = {}

            for provider_name, adapter in adapters.items():
                future = pool.submit(
                    executor.execute,
                    provider_name=provider_name,
                    adapter=adapter,
                    doc=doc,
                    questions=questions,
                    provider_semaphore=None,  # No rate limiting in legacy mode
                    ragas_semaphore=None      # No rate limiting in legacy mode
                )
                future_to_provider[future] = provider_name
                print(f"   ✓ Submitted {provider_name} to thread pool")

            # Collect results as they complete
            print(f"\n⏳ Waiting for {len(adapters)} providers to complete...")
            print(f"   Running in parallel: {', '.join(adapters.keys())}")

            completed_count = 0
            for future in as_completed(future_to_provider):
                provider_name = future_to_provider[future]

                try:
                    result: ProviderResult = future.result()

                    # Store result
                    doc_result.providers[provider_name] = result
                    completed_count += 1

                    # Log completion
                    status_icon = "✅" if result.status == "success" else "❌"
                    print(f"\n   {status_icon} {provider_name} completed ({result.duration_seconds:.1f}s) [{completed_count}/{len(adapters)}]")

                    if result.status == "success":
                        # Print scores
                        scores_str = ", ".join([f"{k}={v:.3f}" for k, v in result.aggregated_scores.items()])
                        print(f"      Scores: {scores_str}")
                    else:
                        print(f"      Error: {result.error}")

                    # Call callback if provided (for saving results)
                    if on_provider_complete:
                        on_provider_complete(result)

                except Exception as e:
                    # Handle thread execution errors
                    print(f"   ❌ {provider_name} thread failed: {e}")

                    # Create error result
                    error_result = ProviderResult(
                        provider=provider_name,
                        doc_id=doc.doc_id,
                        status="error",
                        error=f"Thread execution failed: {str(e)}",
                        timestamp_start=datetime.now().isoformat(),
                        timestamp_end=datetime.now().isoformat()
                    )
                    doc_result.providers[provider_name] = error_result

                    if on_provider_complete:
                        on_provider_complete(error_result)

        # Aggregate results and determine winner
        print(f"\n📊 Aggregating results...")
        doc_result.winner = self._determine_winner(doc_result.providers)

        return doc_result

    def _determine_winner(self, provider_results: Dict[str, ProviderResult]) -> Dict[str, Any]:
        """
        Collect metric scores for each provider (no ranking).

        Args:
            provider_results: Dict of {provider_name: ProviderResult}

        Returns:
            Dict with provider scores
        """
        provider_scores = {}

        for provider_name, result in provider_results.items():
            if result.status == "success":
                provider_scores[provider_name] = result.aggregated_scores

        # Print scores summary
        print(f"\n📊 Provider Scores:")
        for provider_name in sorted(provider_scores.keys()):
            scores = provider_scores[provider_name]

            # Format scores nicely (duration in seconds, others as decimals)
            formatted_scores = []
            for k, v in sorted(scores.items()):
                if k == 'duration_seconds':
                    formatted_scores.append(f"{k}={v:.1f}s")
                else:
                    formatted_scores.append(f"{k}={v:.3f}")
            scores_str = ", ".join(formatted_scores)

            print(f"   {provider_name}: {scores_str}")

        return {"provider_scores": provider_scores}
