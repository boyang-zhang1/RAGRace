"""
Tests for LlamaIndex RAG adapter.

Includes both unit tests (mocked) and integration tests (real API calls).
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import os

from src.adapters.base import Document, RAGResponse
from src.adapters.llamaindex_adapter import LlamaIndexAdapter


# Path to test data
TEST_DATA_DIR = Path(__file__).parent.parent / "data" / "test"
MINI_SQUAD_PATH = TEST_DATA_DIR / "mini_squad.json"


class TestLlamaIndexAdapterUnit:
    """Unit tests for LlamaIndexAdapter (mocked, no real API calls)."""

    def test_adapter_initialization(self):
        """Test adapter can be instantiated."""
        adapter = LlamaIndexAdapter()
        assert adapter is not None
        assert not adapter._initialized

    def test_initialize_without_llamaindex_installed(self):
        """Test initialization fails gracefully if LlamaIndex not installed."""
        adapter = LlamaIndexAdapter()

        with patch('src.adapters.llamaindex_adapter.LLAMAINDEX_AVAILABLE', False):
            with pytest.raises(ImportError, match="LlamaIndex is not installed"):
                adapter.initialize(api_key="test_key")

    @patch('src.adapters.llamaindex_adapter.Settings')
    @patch('src.adapters.llamaindex_adapter.OpenAIEmbedding')
    @patch('src.adapters.llamaindex_adapter.OpenAI')
    def test_initialize_success(self, mock_openai, mock_embedding, mock_settings):
        """Test successful initialization with API key."""
        adapter = LlamaIndexAdapter()
        adapter.initialize(api_key="test_api_key")

        assert adapter._initialized
        assert adapter._api_key == "test_api_key"
        mock_embedding.assert_called_once()
        mock_openai.assert_called_once()

    @patch('src.adapters.llamaindex_adapter.Settings')
    @patch('src.adapters.llamaindex_adapter.OpenAIEmbedding')
    @patch('src.adapters.llamaindex_adapter.OpenAI')
    def test_initialize_with_custom_config(self, mock_openai, mock_embedding, mock_settings):
        """Test initialization with custom configuration."""
        adapter = LlamaIndexAdapter()
        adapter.initialize(
            api_key="test_key",
            embedding_model="text-embedding-ada-002",
            llm_model="gpt-4",
            top_k=5
        )

        assert adapter._top_k == 5
        mock_embedding.assert_called_with(
            model="text-embedding-ada-002",
            api_key="test_key"
        )
        mock_openai.assert_called_with(
            model="gpt-4",
            api_key="test_key"
        )

    def test_ingest_documents_not_initialized(self):
        """Test ingest_documents fails if not initialized."""
        adapter = LlamaIndexAdapter()
        documents = [Document(id="1", content="test", metadata={})]

        with pytest.raises(RuntimeError, match="Adapter not initialized"):
            adapter.ingest_documents(documents)

    def test_ingest_documents_empty_list(self):
        """Test ingest_documents fails with empty document list."""
        adapter = LlamaIndexAdapter()
        adapter._initialized = True  # Bypass initialization

        with pytest.raises(ValueError, match="Documents list cannot be empty"):
            adapter.ingest_documents([])

    @patch('src.adapters.llamaindex_adapter.VectorStoreIndex')
    @patch('src.adapters.llamaindex_adapter.Settings')
    @patch('src.adapters.llamaindex_adapter.OpenAIEmbedding')
    @patch('src.adapters.llamaindex_adapter.OpenAI')
    def test_ingest_documents_success(self, mock_openai, mock_embedding, mock_settings, mock_index_class):
        """Test successful document ingestion."""
        # Setup
        adapter = LlamaIndexAdapter()
        adapter.initialize(api_key="test_key")

        # Mock index creation
        mock_index = MagicMock()
        mock_index.index_id = "test_index_123"
        mock_index_class.from_documents.return_value = mock_index

        # Test documents
        documents = [
            Document(id="doc1", content="This is a test document", metadata={"source": "test"}),
            Document(id="doc2", content="Another test document", metadata={"source": "test"})
        ]

        # Execute
        index_id = adapter.ingest_documents(documents)

        # Verify
        assert index_id == "test_index_123"
        assert index_id in adapter._indices
        mock_index_class.from_documents.assert_called_once()
        assert len(mock_index_class.from_documents.call_args[0][0]) == 2  # 2 documents

    def test_query_not_initialized(self):
        """Test query fails if not initialized."""
        adapter = LlamaIndexAdapter()

        with pytest.raises(RuntimeError, match="Adapter not initialized"):
            adapter.query("test question", "index_123")

    def test_query_invalid_index_id(self):
        """Test query fails with invalid index_id."""
        adapter = LlamaIndexAdapter()
        adapter._initialized = True

        with pytest.raises(KeyError, match="Index .* not found"):
            adapter.query("test question", "nonexistent_index")

    @patch('src.adapters.llamaindex_adapter.Settings')
    @patch('src.adapters.llamaindex_adapter.OpenAIEmbedding')
    @patch('src.adapters.llamaindex_adapter.OpenAI')
    def test_query_success(self, mock_openai, mock_embedding, mock_settings):
        """Test successful query execution."""
        # Setup
        adapter = LlamaIndexAdapter()
        adapter.initialize(api_key="test_key")

        # Mock index and query engine
        mock_index = MagicMock()
        mock_query_engine = MagicMock()
        mock_index.as_query_engine.return_value = mock_query_engine

        # Mock response
        mock_response = MagicMock()
        mock_response.response = "This is the answer"
        mock_source_node_1 = MagicMock()
        mock_source_node_1.node.text = "Context chunk 1"
        mock_source_node_1.score = 0.95
        mock_source_node_2 = MagicMock()
        mock_source_node_2.node.text = "Context chunk 2"
        mock_source_node_2.score = 0.87
        mock_response.source_nodes = [mock_source_node_1, mock_source_node_2]
        mock_query_engine.query.return_value = mock_response

        # Add index to adapter
        adapter._indices["test_index"] = mock_index

        # Execute
        result = adapter.query("What is the answer?", "test_index")

        # Verify
        assert isinstance(result, RAGResponse)
        assert result.answer == "This is the answer"
        assert len(result.context) == 2
        assert result.context[0] == "Context chunk 1"
        assert result.context[1] == "Context chunk 2"
        assert result.latency_ms > 0
        assert result.metadata["num_source_nodes"] == 2
        assert "similarity_scores" in result.metadata

    @patch('src.adapters.llamaindex_adapter.Settings')
    def test_health_check_not_initialized(self, mock_settings):
        """Test health check fails if not initialized."""
        adapter = LlamaIndexAdapter()
        assert not adapter.health_check()

    @patch('src.adapters.llamaindex_adapter.Settings')
    @patch('src.adapters.llamaindex_adapter.OpenAIEmbedding')
    @patch('src.adapters.llamaindex_adapter.OpenAI')
    def test_health_check_success(self, mock_openai, mock_embedding, mock_settings):
        """Test successful health check."""
        adapter = LlamaIndexAdapter()
        adapter.initialize(api_key="test_key")

        # Mock embedding response
        mock_settings.embed_model.get_text_embedding.return_value = [0.1, 0.2, 0.3]

        assert adapter.health_check()


@pytest.mark.integration
class TestLlamaIndexAdapterIntegration:
    """Integration tests for LlamaIndexAdapter (real API calls, requires API key)."""

    @pytest.fixture
    def api_key(self):
        """Get OpenAI API key from environment."""
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            pytest.skip("OPENAI_API_KEY not set - skipping integration test")
        return key

    @pytest.fixture
    def adapter(self, api_key):
        """Create and initialize adapter with real API key."""
        adapter = LlamaIndexAdapter()
        adapter.initialize(api_key=api_key, top_k=2)
        return adapter

    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        return [
            Document(
                id="doc1",
                content="Beyoncé Giselle Knowles-Carter is an American singer, songwriter, and businesswoman. "
                        "She rose to fame in the late 1990s as the lead singer of Destiny's Child, one of "
                        "the best-selling girl groups of all time.",
                metadata={"source": "wikipedia", "topic": "beyonce"}
            ),
            Document(
                id="doc2",
                content="Destiny's Child was formed in 1990 in Houston, Texas. The group's lineup changed "
                        "several times before settling on Beyoncé Knowles, Kelly Rowland, and Michelle Williams.",
                metadata={"source": "wikipedia", "topic": "destinys_child"}
            )
        ]

    def test_end_to_end_workflow(self, adapter, sample_documents):
        """Test complete workflow: initialize -> ingest -> query."""
        # Test health check
        assert adapter.health_check(), "Health check should pass with valid API key"

        # Ingest documents
        index_id = adapter.ingest_documents(sample_documents)
        assert index_id is not None
        assert isinstance(index_id, str)
        assert len(index_id) > 0

        # Query the index
        question = "When did Beyoncé become popular?"
        response = adapter.query(question, index_id)

        # Verify response structure
        assert isinstance(response, RAGResponse)
        assert response.answer is not None
        assert len(response.answer) > 0
        assert isinstance(response.context, list)
        assert len(response.context) > 0
        assert response.latency_ms > 0
        assert isinstance(response.metadata, dict)

        # Verify response content makes sense
        answer_lower = response.answer.lower()
        assert any(keyword in answer_lower for keyword in ["1990", "late", "destiny", "child"]), \
            f"Expected answer to mention time period, got: {response.answer}"

        # Verify context was retrieved
        assert len(response.context) <= 2, "Should retrieve at most top_k=2 chunks"

        # Verify at least one context chunk mentions Beyoncé
        context_text = " ".join(response.context).lower()
        assert "beyoncé" in context_text or "beyonce" in context_text, \
            "Context should mention Beyoncé"

    def test_query_with_different_parameters(self, adapter, sample_documents):
        """Test querying with different similarity_top_k values."""
        # Ingest
        index_id = adapter.ingest_documents(sample_documents)

        # Query with top_k=1
        response1 = adapter.query(
            "What is Destiny's Child?",
            index_id,
            similarity_top_k=1
        )
        assert len(response1.context) <= 1

        # Query with top_k=3
        response2 = adapter.query(
            "What is Destiny's Child?",
            index_id,
            similarity_top_k=3
        )
        assert len(response2.context) <= 3

    def test_multiple_queries_same_index(self, adapter, sample_documents):
        """Test multiple queries on the same index."""
        index_id = adapter.ingest_documents(sample_documents)

        # First query
        response1 = adapter.query("Who is Beyoncé?", index_id)
        assert "beyoncé" in response1.answer.lower() or "beyonce" in response1.answer.lower()

        # Second query
        response2 = adapter.query("What group was she in?", index_id)
        assert len(response2.answer) > 0

        # Third query
        response3 = adapter.query("When was the group formed?", index_id)
        assert len(response3.answer) > 0


if __name__ == "__main__":
    # Run unit tests
    pytest.main([__file__, "-v", "-k", "not integration"])

    # To run integration tests:
    # pytest tests/test_llamaindex_adapter.py -v -m integration
