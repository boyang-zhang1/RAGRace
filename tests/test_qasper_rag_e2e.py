"""
End-to-end RAGRace test with Qasper dataset.

Complete RAGRace workflow - Fair 3-way comparison:
1. Load Qasper document (original PDF from arxiv + questions with ground truth)
2. Upload SAME PDF to ALL 3 RAG providers (LlamaIndex, LandingAI, Reducto)
3. Query ALL 3 providers with SAME questions
4. Evaluate EACH provider's answers against ground truth using Ragas metrics
5. Compare scores across providers and declare winner

Key Design Decisions:
- Uses ORIGINAL PDF from arxiv (not reconstructed from text)
- ALL providers process SAME PDF format (fair comparison)
- Evaluation metrics: Faithfulness, Factual Correctness, Context Recall
- Default: 1 document, 3 questions (configurable for cost control)

Test Results Example (1 document, 3 questions):
- Winner: Reducto (2/3 metrics)
- Reducto: Faithfulness=1.0, Factual_Correctness=0.71, Context_Recall=1.0
- LandingAI: Faithfulness=1.0, Factual_Correctness=0.43, Context_Recall=0.83
- LlamaIndex: Faithfulness=0.0, Factual_Correctness=0.17, Context_Recall=0.0
- Duration: ~2 minutes

Usage:
    # Default test (1 document, 3 questions)
    pytest tests/test_qasper_rag_e2e.py::TestQasperRAGRace::test_ragrace_3_providers_qasper -v -s -m integration

    # Modify max_docs and max_questions in test code for different scale
"""

import pytest
import os
from pathlib import Path

from src.datasets.loader import DatasetLoader
from src.core.ragas_evaluator import RagasEvaluator, RAGEvaluationSample
from src.core.rag_logger import RAGLogger
from src.adapters.llamaindex_adapter import LlamaIndexAdapter
from src.adapters.landingai_adapter import LandingAIAdapter
from src.adapters.reducto_adapter import ReductoAdapter
from src.adapters.base import Document


@pytest.mark.integration
class TestQasperRAGRace:
    """Integration test: Complete RAGRace on Qasper documents."""

    @pytest.fixture
    def openai_api_key(self):
        """Get OpenAI API key."""
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            pytest.skip("OPENAI_API_KEY not set - skipping test")
        return key

    @pytest.fixture
    def llamaindex_api_key(self):
        """Get LlamaIndex Cloud API key."""
        key = os.getenv("LLAMAINDEX_API_KEY")
        if not key:
            pytest.skip("LLAMAINDEX_API_KEY not set - skipping test")
        return key

    @pytest.fixture
    def landingai_api_key(self):
        """Get LandingAI API key."""
        key = os.getenv("VISION_AGENT_API_KEY")
        if not key:
            pytest.skip("VISION_AGENT_API_KEY not set - skipping test")
        return key

    @pytest.fixture
    def reducto_api_key(self):
        """Get Reducto API key."""
        key = os.getenv("REDUCTO_API_KEY")
        if not key:
            pytest.skip("REDUCTO_API_KEY not set - skipping test")
        return key

    @pytest.fixture
    def ragas_evaluator(self):
        """Initialize Ragas evaluator."""
        config = {
            'model': 'gpt-4o-mini',
            'api_key_env': 'OPENAI_API_KEY',
            'metrics': ['faithfulness', 'factual_correctness', 'context_recall']
        }
        return RagasEvaluator(config)

    def test_ragrace_3_providers_qasper(
        self,
        openai_api_key,
        llamaindex_api_key,
        landingai_api_key,
        reducto_api_key,
        ragas_evaluator
    ):
        """
        Complete RAGRace: 3 providers compete on same Qasper document.

        Workflow:
        1. Load 1 document, 3 questions from Qasper
        2. Upload to LlamaIndex (text), LandingAI (PDF), Reducto (PDF)
        3. Query all 3 with same questions
        4. For each question: evaluate all 3 predictions vs ground truth
        5. Compare scores and declare winner

        Args:
            max_docs: Number of documents (default: 1)
            max_questions: Questions per document (default: 3 for demo)
        """
        max_docs = 1
        max_questions = 1

        # Initialize comprehensive logger
        rag_logger = RAGLogger(log_dir="data/results", test_name="qasper_ragrace")

        print("\n" + "=" * 80)
        print("🏁 RAGRACE: 3-WAY PROVIDER COMPARISON ON QASPER")
        print("=" * 80)

        rag_logger.log_section("RAGRACE: 3-WAY PROVIDER COMPARISON ON QASPER")
        rag_logger.log(f"Configuration: {max_docs} documents, {max_questions} questions per document")
        rag_logger.log("")

        # Step 1: Load Qasper documents
        print(f"\n📥 Loading Qasper documents ({max_docs} documents, {max_questions} questions per document)...")
        dataset = DatasetLoader.load_qasper(
            split='train',
            max_docs=max_docs,
            filter_unanswerable=True
        )

        # Group samples by doc_id
        from collections import defaultdict
        docs_dict = defaultdict(list)
        for sample in dataset.samples:
            doc_id = sample.metadata['doc_id']
            docs_dict[doc_id].append(sample)

        # Select documents and questions
        docs_to_test = []
        total_questions = 0
        for doc_id, doc_samples in list(docs_dict.items())[:max_docs]:
            # Take up to max_questions per document
            selected_samples = doc_samples[:max_questions]
            if selected_samples:
                doc_info = {
                    'doc_id': doc_id,
                    'doc_title': selected_samples[0].metadata['doc_title'],
                    'pdf_path': Path(selected_samples[0].metadata['pdf_path']),
                    'samples': selected_samples
                }
                docs_to_test.append(doc_info)
                total_questions += len(selected_samples)
                print(f"✓ Loaded document: {doc_id}")
                print(f"  Title: {doc_info['doc_title'][:80]}...")
                print(f"  PDF: {doc_info['pdf_path']}")
                print(f"  PDF size: {doc_info['pdf_path'].stat().st_size} bytes")
                print(f"  Questions: {len(selected_samples)}")

                # Log document details
                rag_logger.log_document(
                    doc_id=doc_id,
                    doc_title=doc_info['doc_title'],
                    pdf_path=str(doc_info['pdf_path']),
                    pdf_size=doc_info['pdf_path'].stat().st_size,
                    num_questions=len(selected_samples)
                )

        print(f"\n📊 Total: {len(docs_to_test)} documents, {total_questions} questions")

        # Step 2: Initialize ALL 3 RAG providers
        print("\n📦 Initializing ALL 3 RAG providers...")
        adapters = {}

        # LlamaIndex
        adapters['LlamaIndex'] = LlamaIndexAdapter()
        adapters['LlamaIndex'].initialize(
            api_key=openai_api_key,
            llamacloud_api_key=llamaindex_api_key,
            top_k=3
        )
        print("  ✓ LlamaIndex initialized")

        # LandingAI
        adapters['LandingAI'] = LandingAIAdapter()
        adapters['LandingAI'].initialize(
            api_key=landingai_api_key,
            openai_api_key=openai_api_key,
            top_k=3
        )
        print("  ✓ LandingAI initialized")

        # Reducto
        adapters['Reducto'] = ReductoAdapter()
        adapters['Reducto'].initialize(
            api_key=reducto_api_key,
            openai_api_key=openai_api_key,
            top_k=3
        )
        print("  ✓ Reducto initialized")

        # Store all samples for evaluation (per provider)
        provider_samples = {name: [] for name in adapters.keys()}

        # Step 3 & 4: Process each document separately
        for doc_idx, doc in enumerate(docs_to_test, 1):
            doc_id = doc['doc_id']
            doc_title = doc['doc_title']
            pdf_path = doc['pdf_path']
            samples = doc['samples']

            print(f"\n{'='*80}")
            print(f"📄 DOCUMENT {doc_idx}/{len(docs_to_test)}: {doc_id}")
            print(f"{'='*80}")

            # Step 3: Upload this document's PDF to ALL 3 providers
            print(f"\n🔄 Uploading PDF to ALL 3 providers: {pdf_path.name}")
            indices = {}

            # LlamaIndex: Original PDF
            pdf_doc_llama = Document(
                id=doc_id,
                content="",
                metadata={'file_path': str(pdf_path), 'title': doc_title}
            )
            indices['LlamaIndex'] = adapters['LlamaIndex'].ingest_documents([pdf_doc_llama])
            print(f"  ✓ LlamaIndex ingested PDF")

            # LandingAI: Original PDF
            pdf_doc_landingai = Document(
                id=doc_id,
                content="",
                metadata={'file_path': str(pdf_path), 'title': doc_title}
            )
            indices['LandingAI'] = adapters['LandingAI'].ingest_documents([pdf_doc_landingai])
            print(f"  ✓ LandingAI ingested PDF")

            # Reducto: Original PDF
            pdf_doc_reducto = Document(
                id=doc_id,
                content="",
                metadata={'file_path': str(pdf_path), 'title': doc_title}
            )
            indices['Reducto'] = adapters['Reducto'].ingest_documents([pdf_doc_reducto])
            print(f"  ✓ Reducto ingested PDF")

            # Step 4: Query ALL 3 providers with this document's questions
            print(f"\n📝 Querying ALL 3 providers ({len(samples)} questions for this document)...")
            print("=" * 80)

            for i, sample in enumerate(samples, 1):
                question = sample.question
                ground_truth = sample.ground_truth

                print(f"\n❓ Question {i}: {question}")
                print(f"   Ground Truth: {ground_truth[:100]}...")
                print()

                # Log question and ground truth (full text)
                rag_logger.log_question(
                    question_num=i,
                    question=question,
                    ground_truth=ground_truth,
                    question_id=sample.metadata.get('question_id')
                )

                # Query each provider
                for provider_name, adapter in adapters.items():
                    response = adapter.query(question, indices[provider_name])

                    print(f"   {provider_name}:")
                    print(f"     Answer: {response.answer[:100]}...")
                    print(f"     Latency: {response.latency_ms:.0f}ms | Chunks: {len(response.context)}")

                    # Log complete provider response
                    rag_logger.log_provider_response(
                        provider_name=provider_name,
                        answer=response.answer,
                        context_chunks=response.context,
                        latency_ms=response.latency_ms,
                        metadata=response.metadata
                    )

                    # Store for evaluation
                    ragas_sample = RAGEvaluationSample(
                        user_input=question,
                        reference=ground_truth,
                        retrieved_contexts=response.context,
                        response=response.answer,
                        metadata={
                            'provider': provider_name,
                            'latency_ms': response.latency_ms,
                            'question_id': sample.metadata['question_id'],
                            'doc_id': doc_id
                        }
                    )
                    provider_samples[provider_name].append(ragas_sample)

                print("-" * 80)

        # Step 5: Evaluate ALL providers with Ragas
        print("\n" + "=" * 80)
        print("📊 RAGAS EVALUATION - Per Provider")
        print("=" * 80)

        rag_logger.log_section("RAGAS EVALUATION")

        provider_scores = {}
        for provider_name, samples_list in provider_samples.items():
            print(f"\nEvaluating {provider_name}...")
            eval_result = ragas_evaluator.evaluate_samples(samples_list)
            provider_scores[provider_name] = eval_result.scores

            print(f"  {provider_name} Scores:")
            for metric, score in eval_result.scores.items():
                print(f"    {metric}: {score:.4f}")

        # Log aggregated scores
        rag_logger.log_aggregated_scores(provider_scores)

        # Step 6: Compare and declare winner
        print("\n" + "=" * 80)
        print("🏆 RAGRACE RESULTS - PROVIDER COMPARISON")
        print("=" * 80)

        # Compare by each metric
        metrics = list(next(iter(provider_scores.values())).keys())
        overall_winners = []

        for metric in metrics:
            print(f"\n📊 {metric.upper()}:")
            scores = [(name, provider_scores[name][metric]) for name in adapters.keys()]
            scores.sort(key=lambda x: x[1], reverse=True)

            for rank, (name, score) in enumerate(scores, 1):
                medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉"
                print(f"  {medal} {name}: {score:.4f}")

            # Track winner for this metric
            overall_winners.append(scores[0][0])

        # Declare overall winner
        print("\n" + "=" * 80)
        print("🎯 OVERALL WINNER")
        print("=" * 80)

        # Count how many metrics each provider won
        from collections import Counter
        winner_counts = Counter(overall_winners)
        final_winner = winner_counts.most_common(1)[0][0]

        print(f"\n🏆 {final_winner} wins {winner_counts[final_winner]}/{len(metrics)} metrics!")
        print("\nMedal count:")
        for provider_name in adapters.keys():
            count = winner_counts[provider_name]
            print(f"  {provider_name}: {count} 🥇")

        # Log winner
        rag_logger.log_winner(
            winner=final_winner,
            winner_counts=winner_counts,
            total_metrics=len(metrics)
        )

        # No cleanup needed - using original PDF from arxiv

        print("\n" + "=" * 80)
        print("✅ RAGRACE COMPLETE!")
        print(f"   Tested: {len(docs_to_test)} documents, {total_questions} questions")
        print("=" * 80)

        # Close logger
        rag_logger.close()

        # Assertions
        assert len(provider_scores) == 3, "Should have scores for all 3 providers"
        for provider_name in adapters.keys():
            assert provider_name in provider_scores
            assert len(provider_scores[provider_name]) > 0
            # Verify each provider was tested on all questions
            assert len(provider_samples[provider_name]) == total_questions, \
                f"{provider_name} should have {total_questions} samples"


if __name__ == "__main__":
    """
    Run the RAGRace:

    pytest tests/test_qasper_rag_e2e.py::TestQasperRAGRace::test_ragrace_3_providers_qasper -v -s -m integration
    """
    pytest.main([__file__, "-v", "-s", "-m", "integration"])
