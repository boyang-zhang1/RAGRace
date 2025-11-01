"""
Tests for Reducto RAG adapter.

Includes both unit tests (mocked) and integration tests (real API calls).
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import os

from src.adapters.base import Document, RAGResponse
from src.adapters.reducto_adapter import ReductoAdapter


# Path to test data
TEST_DATA_DIR = Path(__file__).parent.parent / "data" / "test"


class TestReductoAdapterUnit:
    """Unit tests for ReductoAdapter (mocked, no real API calls)."""

    def test_adapter_initialization(self):
        """Test adapter can be instantiated."""
        adapter = ReductoAdapter()
        assert adapter is not None
        assert not adapter._initialized

    def test_initialize_without_openai_installed(self):
        """Test initialization fails gracefully if OpenAI not installed."""
        adapter = ReductoAdapter()

        with patch('src.adapters.reducto_adapter.OPENAI_AVAILABLE', False):
            with pytest.raises(ImportError, match="OpenAI is required"):
                adapter.initialize(api_key="test_key", openai_api_key="test_openai_key")

    def test_initialize_without_openai_key(self):
        """Test initialization fails without OpenAI API key."""
        adapter = ReductoAdapter()

        with pytest.raises(ValueError, match="openai_api_key is required"):
            adapter.initialize(api_key="test_reducto_key")

    @patch('src.adapters.reducto_adapter.OpenAI')
    def test_initialize_success(self, mock_openai_class):
        """Test successful initialization with API keys."""
        adapter = ReductoAdapter()
        adapter.initialize(
            api_key="test_reducto_key",
            openai_api_key="test_openai_key"
        )

        assert adapter._initialized
        assert adapter._api_key == "test_reducto_key"
        mock_openai_class.assert_called_once_with(api_key="test_openai_key")

    @patch('src.adapters.reducto_adapter.OpenAI')
    def test_initialize_with_custom_config(self, mock_openai_class):
        """Test initialization with custom configuration."""
        adapter = ReductoAdapter()
        adapter.initialize(
            api_key="test_key",
            openai_api_key="test_openai_key",
            embedding_model="text-embedding-ada-002",
            llm_model="gpt-4",
            top_k=5,
            chunk_mode="disabled",
            summarize_figures=False
        )

        assert adapter._top_k == 5
        assert adapter._embedding_model == "text-embedding-ada-002"
        assert adapter._llm_model == "gpt-4"
        assert adapter._chunk_mode == "disabled"
        assert adapter._summarize_figures == False

    def test_ingest_documents_not_initialized(self):
        """Test ingest_documents fails if not initialized."""
        adapter = ReductoAdapter()
        documents = [Document(id="1", content="test", metadata={})]

        with pytest.raises(RuntimeError, match="Adapter not initialized"):
            adapter.ingest_documents(documents)

    def test_ingest_documents_empty_list(self):
        """Test ingest_documents fails with empty document list."""
        adapter = ReductoAdapter()
        adapter._initialized = True  # Bypass initialization

        with pytest.raises(ValueError, match="Documents list cannot be empty"):
            adapter.ingest_documents([])

    def test_query_not_initialized(self):
        """Test query fails if not initialized."""
        adapter = ReductoAdapter()

        with pytest.raises(RuntimeError, match="Adapter not initialized"):
            adapter.query("test question", "index_123")

    def test_query_invalid_index_id(self):
        """Test query fails with invalid index_id."""
        adapter = ReductoAdapter()
        adapter._initialized = True

        with pytest.raises(KeyError, match="Index .* not found"):
            adapter.query("test question", "nonexistent_index")

    @patch('src.adapters.reducto_adapter.OpenAI')
    def test_health_check_success(self, mock_openai_class):
        """Test successful health check."""
        adapter = ReductoAdapter()
        adapter.initialize(api_key="test_key", openai_api_key="test_openai_key")

        assert adapter.health_check()

    def test_health_check_not_initialized(self):
        """Test health check fails if not initialized."""
        adapter = ReductoAdapter()
        assert not adapter.health_check()


@pytest.mark.integration
class TestReductoAdapterIntegration:
    """Integration tests for ReductoAdapter (real API calls, requires API keys)."""

    @pytest.fixture
    def reducto_api_key(self):
        """Get Reducto API key from environment."""
        key = os.getenv("REDUCTO_API_KEY")
        if not key:
            pytest.skip("REDUCTO_API_KEY not set - skipping integration test")
        return key

    @pytest.fixture
    def openai_api_key(self):
        """Get OpenAI API key from environment."""
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            pytest.skip("OPENAI_API_KEY not set - skipping integration test")
        return key

    @pytest.fixture
    def adapter(self, reducto_api_key, openai_api_key):
        """Create and initialize adapter with real API keys."""
        adapter = ReductoAdapter()
        adapter.initialize(
            api_key=reducto_api_key,
            openai_api_key=openai_api_key,
            top_k=2,
            chunk_mode="variable",
            summarize_figures=True
        )
        return adapter

    @pytest.fixture
    def sample_document_with_url(self):
        """Create a sample document using a public PDF URL."""
        # Using a simple, short public PDF for testing
        return [
            Document(
                id="test_doc",
                content="Sample document",  # Not used, document_url is used instead
                metadata={
                    "document_url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
                    "source": "test"
                }
            )
        ]

    def test_health_check(self, adapter):
        """Test health check with real API."""
        result = adapter.health_check()
        assert result, "Health check should pass with valid API key"

    def test_end_to_end_workflow(self, adapter, sample_document_with_url):
        """Test complete workflow: initialize -> ingest -> query."""
        # Test health check
        assert adapter.health_check(), "Health check should pass with valid API key"

        # Ingest document
        print(f"\n[TEST] Ingesting document via Reducto...")
        index_id = adapter.ingest_documents(sample_document_with_url)
        assert index_id is not None
        assert isinstance(index_id, str)
        assert len(index_id) > 0
        print(f"[TEST] Created index: {index_id}")

        # Query 1: Simple factual question
        print(f"\n[TEST] Query 1: What is this document?")
        question1 = "What is this document?"
        response1 = adapter.query(question1, index_id)

        # Verify response structure
        assert isinstance(response1, RAGResponse)
        assert response1.answer is not None
        assert len(response1.answer) > 0
        assert isinstance(response1.context, list)
        assert len(response1.context) > 0
        assert response1.latency_ms > 0
        assert isinstance(response1.metadata, dict)

        print(f"[TEST] Answer 1: {response1.answer}")
        print(f"[TEST] Retrieved {len(response1.context)} context chunks")
        print(f"[TEST] Latency: {response1.latency_ms:.2f}ms")
        print(f"[TEST] Avg similarity score: {response1.metadata.get('avg_similarity_score', 'N/A')}")

        # Query 2: Different question
        print(f"\n[TEST] Query 2: What type of document is this?")
        question2 = "What type of document is this?"
        response2 = adapter.query(question2, index_id)

        # Verify second response
        assert isinstance(response2, RAGResponse)
        assert response2.answer is not None
        assert len(response2.answer) > 0
        assert len(response2.context) > 0

        print(f"[TEST] Answer 2: {response2.answer}")
        print(f"[TEST] Retrieved {len(response2.context)} context chunks")
        print(f"[TEST] Latency: {response2.latency_ms:.2f}ms")

        # Verify context was retrieved (should have at most top_k=2 chunks)
        assert len(response1.context) <= 2, "Should retrieve at most top_k=2 chunks"
        assert len(response2.context) <= 2, "Should retrieve at most top_k=2 chunks"

        print(f"\n[TEST] ✓ End-to-end workflow completed successfully")

    def test_query_with_different_top_k(self, adapter, sample_document_with_url):
        """Test querying with different top_k values."""
        # Ingest
        print(f"\n[TEST] Testing different top_k values...")
        index_id = adapter.ingest_documents(sample_document_with_url)

        # Query with top_k=1
        response1 = adapter.query(
            "What is this document?",
            index_id,
            top_k=1
        )
        assert len(response1.context) <= 1
        print(f"[TEST] top_k=1: Retrieved {len(response1.context)} chunks")

        # Query with top_k=3
        response2 = adapter.query(
            "What is this document?",
            index_id,
            top_k=3
        )
        assert len(response2.context) <= 3
        print(f"[TEST] top_k=3: Retrieved {len(response2.context)} chunks")

    def test_query_with_enriched_content(self, adapter, sample_document_with_url):
        """Test querying with AI-enriched content enabled."""
        # Ingest
        print(f"\n[TEST] Testing enriched content...")
        index_id = adapter.ingest_documents(sample_document_with_url)

        # Query with enriched content
        response = adapter.query(
            "What is this document?",
            index_id,
            use_enriched=True
        )

        # Verify response
        assert isinstance(response, RAGResponse)
        assert response.metadata.get("used_enriched_content") == True
        print(f"[TEST] Used enriched content: {response.metadata.get('used_enriched_content')}")


if __name__ == "__main__":
    # Run unit tests
    pytest.main([__file__, "-v", "-k", "not integration"])

    # To run integration tests:
    # pytest tests/test_reducto_adapter.py -v -m integration -s
