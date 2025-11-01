"""
Integration tests for RAG evaluation pipeline.

Tests end-to-end evaluation of multiple RAG providers using Ragas metrics.
Compares LlamaIndex, LandingAI, and Reducto on real questions from mini_squad.json.
"""

import pytest
import os
import json
from pathlib import Path
from typing import List, Dict, Any

from src.datasets.loader import DatasetLoader
from src.core.ragas_evaluator import RagasEvaluator, RAGEvaluationSample
from src.core.scorer import Scorer
from src.adapters.base import Document, RAGResponse
from src.adapters.llamaindex_adapter import LlamaIndexAdapter
from src.adapters.landingai_adapter import LandingAIAdapter
from src.adapters.reducto_adapter import ReductoAdapter
from src.utils.pdf_generator import squad_context_to_pdf


# Path to test data
TEST_DATA_DIR = Path(__file__).parent.parent / "data" / "test"
MINI_SQUAD_PATH = TEST_DATA_DIR / "mini_squad.json"
TEMP_PDF_DIR = TEST_DATA_DIR / "temp_pdfs"


@pytest.mark.integration
class TestEvaluationIntegration:
    """Integration tests for RAG evaluation pipeline with multiple providers."""

    @pytest.fixture
    def openai_api_key(self):
        """Get OpenAI API key for LlamaIndex."""
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            pytest.skip("OPENAI_API_KEY not set - skipping integration test")
        return key

    @pytest.fixture
    def landingai_api_key(self):
        """Get LandingAI API key."""
        key = os.getenv("VISION_AGENT_API_KEY")
        if not key:
            pytest.skip("VISION_AGENT_API_KEY not set - skipping integration test")
        return key

    @pytest.fixture
    def reducto_api_key(self):
        """Get Reducto API key."""
        key = os.getenv("REDUCTO_API_KEY")
        if not key:
            pytest.skip("REDUCTO_API_KEY not set - skipping integration test")
        return key

    @pytest.fixture
    def squad_dataset(self):
        """Load mini_squad.json dataset."""
        loader = DatasetLoader('squad')
        dataset = loader.load(str(MINI_SQUAD_PATH), max_samples=2)  # Use only 2 questions to save cost
        return dataset

    @pytest.fixture
    def ragas_evaluator(self):
        """Initialize Ragas evaluator."""
        config = {
            'model': 'gpt-4o-mini',
            'api_key_env': 'OPENAI_API_KEY',
            'metrics': ['faithfulness', 'factual_correctness', 'context_recall']
        }
        return RagasEvaluator(config)

    def test_compare_providers_with_ragas(
        self,
        openai_api_key,
        squad_dataset,
        ragas_evaluator
    ):
        """
        Evaluate LlamaIndex RAG provider using Ragas evaluation metrics.

        NOTE: This test focuses on LlamaIndex only because:
        - LlamaIndex: Full RAG framework, supports plain text ingestion
        - LandingAI/Reducto: Document preprocessing providers, require files (PDF/images)

        For fair comparison on SQuAD text data, we test LlamaIndex which can ingest
        the plain text context directly. LandingAI/Reducto have their own integration
        tests with document-based inputs.

        This test:
        1. Loads 2 questions from mini_squad.json
        2. Runs LlamaIndex on the questions
        3. Evaluates with Ragas metrics (Faithfulness, FactualCorrectness, ContextRecall)
        4. Validates Ragas evaluation pipeline works end-to-end
        """
        print("\n" + "=" * 80)
        print("RAG PROVIDER EVALUATION - CP4 Integration Test")
        print("Testing: LlamaIndex with Ragas Evaluation")
        print("=" * 80)

        # Prepare context document from SQuAD dataset
        # Use the full context as the document to ingest
        context_text = None
        with open(MINI_SQUAD_PATH) as f:
            data = json.load(f)
            context_text = data['data'][0]['paragraphs'][0]['context']

        doc = Document(
            id="beyonce_context",
            content=context_text,
            metadata={"source": "squad", "title": "Beyoncé"}
        )

        # Initialize LlamaIndex adapter
        print("\n📦 Initializing LlamaIndex adapter...")
        adapter = LlamaIndexAdapter()
        adapter.initialize(api_key=openai_api_key, top_k=2)

        # Verify adapter is healthy
        assert adapter.health_check(), "LlamaIndex adapter failed health check"
        print(f"  ✓ LlamaIndex adapter initialized")

        # Ingest document
        print("\n📥 Ingesting document...")
        index_id = adapter.ingest_documents([doc])
        print(f"  ✓ LlamaIndex ingested document (index: {index_id[:20]}...)")

        # Prepare evaluation samples
        ragas_samples = []

        # Query adapter and collect responses
        print(f"\n🔍 Querying LlamaIndex ({len(squad_dataset.samples)} questions)...")
        for i, sample in enumerate(squad_dataset.samples, 1):
            question = sample.question
            reference = sample.ground_truth

            print(f"\n  Question {i}: {question}")
            print(f"  Ground Truth: {reference}")

            # Query the adapter
            response: RAGResponse = adapter.query(question, index_id)

            print(f"    Answer: {response.answer}")
            print(f"    Retrieved {len(response.context)} chunks")
            print(f"    Latency: {response.latency_ms:.2f}ms")

            # Convert to Ragas format
            ragas_sample = RAGEvaluationSample(
                user_input=question,
                reference=reference,
                retrieved_contexts=response.context,
                response=response.answer,
                metadata={'provider': 'LlamaIndex', 'latency_ms': response.latency_ms}
            )
            ragas_samples.append(ragas_sample)

        # Evaluate with Ragas
        print("\n" + "=" * 80)
        print("📊 RAGAS EVALUATION RESULTS")
        print("=" * 80)

        print(f"\nEvaluating LlamaIndex with Ragas metrics...")
        eval_result = ragas_evaluator.evaluate_samples(ragas_samples)

        print(f"\nLlamaIndex Scores:")
        for metric, score in eval_result.scores.items():
            print(f"  {metric}: {score:.4f}")

        # Assertions - verify evaluation completed successfully
        assert len(eval_result.scores) > 0, "No scores returned from evaluation"

        # Check that key metrics are present (allowing for mode suffixes like "factual_correctness(mode=f1)")
        expected_base_metrics = ['faithfulness', 'factual_correctness', 'context_recall']
        for base_metric in expected_base_metrics:
            # Check if metric exists exactly or with a mode suffix
            matching_metrics = [m for m in eval_result.scores.keys() if m.startswith(base_metric)]
            assert len(matching_metrics) > 0, f"Missing metric family: {base_metric}"

            # Verify scores are in valid range [0, 1]
            for metric_name in matching_metrics:
                score = eval_result.scores[metric_name]
                assert 0 <= score <= 1, f"{metric_name} score {score} out of range [0, 1]"

        print("\n" + "=" * 80)
        print("✅ CP4 EVALUATION COMPLETE")
        print("=" * 80)

    def test_all_providers_comparison(
        self,
        openai_api_key,
        landingai_api_key,
        reducto_api_key,
        squad_dataset,
        ragas_evaluator
    ):
        """
        Compare ALL 3 RAG providers on the same SQuAD content.

        This test:
        1. Converts SQuAD context to PDF
        2. Tests LlamaIndex with text
        3. Tests LandingAI with PDF
        4. Tests Reducto with PDF
        5. Evaluates all with Ragas
        6. Compares results side-by-side
        """
        print("\n" + "=" * 80)
        print("COMPREHENSIVE RAG PROVIDER COMPARISON")
        print("Testing ALL 3 Providers on Same SQuAD Content")
        print("=" * 80)

        # Load SQuAD context
        with open(MINI_SQUAD_PATH) as f:
            data = json.load(f)
            context_text = data['data'][0]['paragraphs'][0]['context']
            article_title = data['data'][0]['title']

        print(f"\n📄 Test Document: {article_title}")
        print(f"   Context length: {len(context_text)} characters")

        # Create PDF from context for document-based providers
        print("\n📄 Generating PDF from SQuAD context...")
        TEMP_PDF_DIR.mkdir(parents=True, exist_ok=True)
        pdf_path = TEMP_PDF_DIR / "beyonce_context.pdf"

        squad_context_to_pdf(
            context=context_text,
            output_path=str(pdf_path),
            title=article_title
        )
        print(f"   ✓ PDF created: {pdf_path}")

        # Initialize all 3 adapters
        print("\n📦 Initializing ALL adapters...")
        adapters = {}

        # LlamaIndex - text-based
        adapters['LlamaIndex'] = LlamaIndexAdapter()
        adapters['LlamaIndex'].initialize(api_key=openai_api_key, top_k=2)

        # LandingAI - document-based
        adapters['LandingAI'] = LandingAIAdapter()
        adapters['LandingAI'].initialize(
            api_key=landingai_api_key,
            openai_api_key=openai_api_key,
            top_k=2
        )

        # Reducto - document-based
        adapters['Reducto'] = ReductoAdapter()
        adapters['Reducto'].initialize(
            api_key=reducto_api_key,
            openai_api_key=openai_api_key,
            top_k=2
        )

        # Verify all adapters are healthy
        for name, adapter in adapters.items():
            assert adapter.health_check(), f"{name} adapter failed health check"
            print(f"  ✓ {name} initialized")

        # Ingest documents
        print("\n📥 Ingesting documents...")
        indices = {}

        # LlamaIndex: Plain text
        text_doc = Document(
            id="beyonce_context",
            content=context_text,
            metadata={"source": "squad", "title": article_title}
        )
        indices['LlamaIndex'] = adapters['LlamaIndex'].ingest_documents([text_doc])
        print(f"  ✓ LlamaIndex ingested text ({len(context_text)} chars)")

        # LandingAI: PDF file
        pdf_doc_landingai = Document(
            id="beyonce_pdf",
            content="",  # Not used for file-based
            metadata={
                "file_path": str(pdf_path),
                "source": "squad",
                "title": article_title
            }
        )
        indices['LandingAI'] = adapters['LandingAI'].ingest_documents([pdf_doc_landingai])
        print(f"  ✓ LandingAI ingested PDF ({pdf_path.stat().st_size} bytes)")

        # Reducto: PDF file
        pdf_doc_reducto = Document(
            id="beyonce_pdf",
            content="",  # Not used for file-based
            metadata={
                "file_path": str(pdf_path),
                "source": "squad",
                "title": article_title
            }
        )
        indices['Reducto'] = adapters['Reducto'].ingest_documents([pdf_doc_reducto])
        print(f"  ✓ Reducto ingested PDF ({pdf_path.stat().st_size} bytes)")

        # Query all adapters and collect responses
        print(f"\n🔍 Querying ALL adapters ({len(squad_dataset.samples)} questions)...")
        provider_samples = {name: [] for name in adapters.keys()}

        for i, sample in enumerate(squad_dataset.samples, 1):
            question = sample.question
            reference = sample.ground_truth

            print(f"\n  Question {i}: {question}")
            print(f"  Ground Truth: {reference}\n")

            for name, adapter in adapters.items():
                # Query the adapter
                response: RAGResponse = adapter.query(question, indices[name])

                print(f"    {name}:")
                print(f"      Answer: {response.answer}")
                print(f"      Retrieved {len(response.context)} chunks")
                print(f"      Latency: {response.latency_ms:.2f}ms")

                # Convert to Ragas format
                ragas_sample = RAGEvaluationSample(
                    user_input=question,
                    reference=reference,
                    retrieved_contexts=response.context,
                    response=response.answer,
                    metadata={'provider': name, 'latency_ms': response.latency_ms}
                )
                provider_samples[name].append(ragas_sample)

        # Evaluate each provider with Ragas
        print("\n" + "=" * 80)
        print("📊 RAGAS EVALUATION RESULTS")
        print("=" * 80)

        results = {}
        for name, samples in provider_samples.items():
            print(f"\nEvaluating {name}...")
            eval_result = ragas_evaluator.evaluate_samples(samples)
            results[name] = eval_result.scores

            print(f"\n  {name} Scores:")
            for metric, score in eval_result.scores.items():
                print(f"    {metric}: {score:.4f}")

        # Compare results
        print("\n" + "=" * 80)
        print("🏆 PROVIDER COMPARISON")
        print("=" * 80)

        # Find best provider for each metric
        metrics = list(next(iter(results.values())).keys())
        for metric in metrics:
            print(f"\n{metric.upper()}:")
            scores = [(name, results[name][metric]) for name in adapters.keys()]
            scores.sort(key=lambda x: x[1], reverse=True)

            for rank, (name, score) in enumerate(scores, 1):
                medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉"
                print(f"  {medal} {name}: {score:.4f}")

        # Assertions
        for name in adapters.keys():
            assert name in results
            assert len(results[name]) > 0

        # Cleanup: Remove temporary PDF
        if pdf_path.exists():
            pdf_path.unlink()
            print(f"\n🧹 Cleaned up temporary PDF: {pdf_path}")

        print("\n" + "=" * 80)
        print("✅ COMPREHENSIVE EVALUATION COMPLETE")
        print("=" * 80)

    def test_gpt_batch_scorer(
        self,
        openai_api_key,
        squad_dataset
    ):
        """
        Optional test: Evaluate LlamaIndex using GPT batch scorer.

        This demonstrates an alternative scoring method using GPT structured outputs.
        Compares LlamaIndex predictions against ground truth using semantic similarity.
        """
        print("\n" + "=" * 80)
        print("GPT BATCH SCORER TEST")
        print("=" * 80)

        # Load scoring config
        import yaml
        config_path = Path(__file__).parent.parent / "config" / "scoring.yaml"
        with open(config_path) as f:
            scoring_config = yaml.safe_load(f)['scoring']

        # Note: config uses gpt-5-nano which doesn't exist yet, update to real model
        scoring_config['model'] = 'gpt-4o-mini'
        scorer = Scorer(scoring_config)

        # Prepare context document
        context_text = None
        with open(MINI_SQUAD_PATH) as f:
            data = json.load(f)
            context_text = data['data'][0]['paragraphs'][0]['context']

        doc = Document(
            id="beyonce_context",
            content=context_text,
            metadata={"source": "squad"}
        )

        # Initialize LlamaIndex adapter
        adapter = LlamaIndexAdapter()
        adapter.initialize(api_key=openai_api_key, top_k=2)

        # Ingest document
        index_id = adapter.ingest_documents([doc])

        # Test on first question only (cost control)
        sample = squad_dataset.samples[0]
        question = sample.question
        ground_truth = sample.ground_truth

        print(f"\nQuestion: {question}")
        print(f"Ground Truth: {ground_truth}\n")

        # Get prediction from LlamaIndex
        response = adapter.query(question, index_id)
        prediction = response.answer
        print(f"LlamaIndex Answer: {prediction}")

        # For batch scorer demo, create a mock comparison with variations
        predictions = {
            'LlamaIndex': prediction,
            'Mock_Perfect': ground_truth,  # Should score 100
            'Mock_Wrong': "She became popular in 2050"  # Should score low
        }

        # Score with GPT batch scorer
        print("\n📊 GPT Batch Scores (0-100):")
        scores = scorer.score_batch(question, ground_truth, predictions)

        # Sort by score
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        for rank, (name, score) in enumerate(sorted_scores, 1):
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉"
            print(f"  {medal} {name}: {score}/100")

        # Also compute exact match
        print("\n📊 Exact Match Scores:")
        for name, pred in predictions.items():
            em_score = scorer.compute_exact_match(ground_truth, pred)
            print(f"  {name}: {em_score} (1=exact match, 0=no match)")

        # Verify scores are valid
        for name, score in scores.items():
            assert 0 <= score <= 100
            assert isinstance(score, int)

        # Verify Mock_Perfect scores highest
        assert scores['Mock_Perfect'] >= scores['LlamaIndex']
        assert scores['Mock_Perfect'] >= scores['Mock_Wrong']

        print("\n✅ GPT Batch Scorer Test Complete")


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-m", "integration", "-s"])
