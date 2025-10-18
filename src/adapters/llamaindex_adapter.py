"""
LlamaIndex RAG Provider Adapter.

Implements BaseAdapter interface for LlamaIndex framework.
Based on actual API documentation from https://docs.llamaindex.ai/
"""

import time
from typing import List, Dict, Optional
import logging

from src.adapters.base import BaseAdapter, Document as RAGDocument, RAGResponse

# LlamaIndex imports
try:
    from llama_index.core import VectorStoreIndex, Document as LlamaDocument, Settings
    from llama_index.embeddings.openai import OpenAIEmbedding
    from llama_index.llms.openai import OpenAI
    from llama_parse import LlamaParse
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False

logger = logging.getLogger(__name__)


class LlamaIndexAdapter(BaseAdapter):
    """
    Adapter for LlamaIndex RAG framework.

    Uses VectorStoreIndex with in-memory storage for document retrieval.
    Configured to use OpenAI for embeddings and LLM by default.
    """

    def __init__(self):
        """Initialize the adapter."""
        self._indices: Dict[str, VectorStoreIndex] = {}  # Map index_id -> VectorStoreIndex
        self._initialized = False
        self._api_key: Optional[str] = None
        self._llamacloud_api_key: Optional[str] = None

    def initialize(self, api_key: str, **kwargs) -> None:
        """
        Initialize the LlamaIndex adapter with API credentials.

        Args:
            api_key: OpenAI API key (used for both embeddings and LLM)
            **kwargs: Additional configuration options:
                - llamacloud_api_key: LlamaCloud API key for LlamaParse (required for PDF parsing)
                - embedding_model: OpenAI embedding model (default: "text-embedding-3-small")
                - llm_model: OpenAI LLM model (default: "gpt-4o-mini")
                - chunk_size: Chunk size for document splitting (default: 1024)
                - chunk_overlap: Overlap between chunks (default: 20)
                - top_k: Number of nodes to retrieve (default: 3)
        """
        if not LLAMAINDEX_AVAILABLE:
            raise ImportError(
                "LlamaIndex is not installed. Install with: "
                "pip install llama-index-core llama-index-embeddings-openai llama-index-llms-openai llama-parse"
            )

        self._api_key = api_key
        self._llamacloud_api_key = kwargs.get("llamacloud_api_key")

        if not self._llamacloud_api_key:
            raise ValueError("llamacloud_api_key is required for PDF parsing with LlamaParse")

        # Extract configuration
        embedding_model = kwargs.get("embedding_model", "text-embedding-3-small")
        llm_model = kwargs.get("llm_model", "gpt-4o-mini")
        self._top_k = kwargs.get("top_k", 3)

        # Configure LlamaIndex Settings (global configuration)
        Settings.embed_model = OpenAIEmbedding(
            model=embedding_model,
            api_key=api_key
        )

        Settings.llm = OpenAI(
            model=llm_model,
            api_key=api_key
        )

        # Optional: Configure chunk size if provided
        if "chunk_size" in kwargs:
            from llama_index.core.node_parser import SentenceSplitter
            Settings.node_parser = SentenceSplitter(
                chunk_size=kwargs["chunk_size"],
                chunk_overlap=kwargs.get("chunk_overlap", 20)
            )

        self._initialized = True
        logger.info(
            f"LlamaIndex adapter initialized with embedding_model={embedding_model}, "
            f"llm_model={llm_model}, top_k={self._top_k}"
        )

    def ingest_documents(self, documents: List[RAGDocument]) -> str:
        """
        Ingest documents into LlamaIndex and create a vector index.

        Args:
            documents: List of documents to ingest

        Returns:
            index_id: Unique identifier for the created index

        Raises:
            RuntimeError: If adapter not initialized
            ValueError: If documents list is empty
        """
        if not self._initialized:
            raise RuntimeError("Adapter not initialized. Call initialize() first.")

        if not documents:
            raise ValueError("Documents list cannot be empty")

        # Convert RAGRace documents to LlamaIndex documents
        llama_docs = []
        for doc in documents:
            # STRICT: Only process PDF files (no silent fallback to text)
            if "file_path" not in doc.metadata or not doc.metadata["file_path"]:
                error_msg = (
                    f"Document {doc.id} missing 'file_path' in metadata. "
                    f"LlamaIndex adapter requires PDF files for LlamaParse cloud API. "
                    f"Got metadata: {list(doc.metadata.keys())}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

            file_path = doc.metadata["file_path"]

            # Validate PDF file extension
            if not str(file_path).lower().endswith('.pdf'):
                error_msg = (
                    f"Document {doc.id} has non-PDF file: {file_path}. "
                    f"LlamaIndex adapter requires PDF files for LlamaParse cloud API."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Load PDF using LlamaParse cloud API (for proper PDF text extraction)
            logger.info(f"Loading PDF file via LlamaParse cloud API: {file_path}")

            try:
                # Initialize LlamaParse with cloud API key
                parser = LlamaParse(
                    api_key=self._llamacloud_api_key,
                    result_type="markdown",  # Use markdown for better structure preservation
                    verbose=False
                )

                # Parse PDF via cloud API
                pdf_docs = parser.load_data(file_path)

                # Update metadata with original doc_id
                for pdf_doc in pdf_docs:
                    pdf_doc.doc_id = doc.id
                    # Merge metadata from RAGDocument
                    pdf_doc.metadata.update(doc.metadata)

                llama_docs.extend(pdf_docs)
                logger.info(f"Loaded {len(pdf_docs)} document(s) from {file_path}")
            except Exception as e:
                logger.error(f"Failed to load PDF {file_path}: {e}")
                raise

        logger.info(f"Ingesting {len(llama_docs)} documents into LlamaIndex")

        # Build vector index (automatically chunks and embeds documents)
        start_time = time.time()
        index = VectorStoreIndex.from_documents(
            llama_docs,
            show_progress=False
        )
        ingest_time = time.time() - start_time

        # Store index in memory
        index_id = index.index_id
        self._indices[index_id] = index

        logger.info(
            f"Created index {index_id} with {len(documents)} documents "
            f"in {ingest_time:.2f}s"
        )

        return index_id

    def query(self, question: str, index_id: str, **kwargs) -> RAGResponse:
        """
        Query the RAG system with a question.

        Args:
            question: The question to ask
            index_id: The index identifier returned from ingest_documents()
            **kwargs: Additional query options:
                - similarity_top_k: Override default top_k for this query
                - response_mode: How to synthesize response (default: "compact")

        Returns:
            RAGResponse: Standardized response with answer, context, and metadata

        Raises:
            RuntimeError: If adapter not initialized
            KeyError: If index_id not found
        """
        if not self._initialized:
            raise RuntimeError("Adapter not initialized. Call initialize() first.")

        if index_id not in self._indices:
            raise KeyError(f"Index {index_id} not found. Did you call ingest_documents()?")

        index = self._indices[index_id]

        # Get query parameters
        similarity_top_k = kwargs.get("similarity_top_k", self._top_k)
        response_mode = kwargs.get("response_mode", "compact")

        logger.info(f"Querying index {index_id} with question: {question[:50]}...")

        # Create query engine
        query_engine = index.as_query_engine(
            similarity_top_k=similarity_top_k,
            response_mode=response_mode
        )

        # Execute query and measure latency
        start_time = time.time()
        response = query_engine.query(question)
        latency_ms = (time.time() - start_time) * 1000

        # Extract answer
        answer = str(response.response)

        # Extract retrieved context chunks
        context_chunks = []
        for source_node in response.source_nodes:
            context_chunks.append(source_node.node.text)

        # Extract metadata
        metadata = {
            "index_id": index_id,
            "similarity_top_k": similarity_top_k,
            "num_source_nodes": len(response.source_nodes),
            "response_mode": response_mode
        }

        # Add scores if available
        if response.source_nodes:
            scores = [node.score for node in response.source_nodes if node.score is not None]
            if scores:
                metadata["similarity_scores"] = scores
                metadata["avg_similarity_score"] = sum(scores) / len(scores)

        logger.info(
            f"Query completed in {latency_ms:.2f}ms, "
            f"retrieved {len(context_chunks)} context chunks"
        )

        return RAGResponse(
            answer=answer,
            context=context_chunks,
            metadata=metadata,
            latency_ms=latency_ms,
            tokens_used=None  # LlamaIndex doesn't expose token count easily in response
        )

    def health_check(self) -> bool:
        """
        Check if LlamaIndex is accessible and properly configured.

        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            # Check if LlamaIndex is available
            if not LLAMAINDEX_AVAILABLE:
                logger.error("LlamaIndex not installed")
                return False

            # Check if initialized
            if not self._initialized:
                logger.error("Adapter not initialized")
                return False

            # Test embedding with a simple call
            test_text = "health check test"
            embedding = Settings.embed_model.get_text_embedding(test_text)

            if not embedding or len(embedding) == 0:
                logger.error("Embedding returned empty result")
                return False

            logger.info("Health check passed")
            return True

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
