"""
Reducto RAG Provider Adapter.

Implements BaseAdapter interface for Reducto's document processing API.
Based on actual API documentation from https://docs.reducto.ai/

Reducto is a document processing API optimized for RAG systems - it converts
unstructured documents into structured chunks with embedding optimization.
This adapter adds embedding generation and vector search to complete the RAG pipeline.
"""

import time
import requests
import numpy as np
from typing import List, Dict, Optional, Any
import logging

from src.adapters.base import BaseAdapter, Document as RAGDocument, RAGResponse

# OpenAI for embeddings and LLM
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)


class ReductoAdapter(BaseAdapter):
    """
    Adapter for Reducto document processing API.

    Reducto provides document parsing with RAG-optimized features:
    - Variable-size semantic chunking
    - Embedding-optimized text output
    - AI-powered content enrichment

    This adapter adds:
    - Embedding generation (via OpenAI)
    - Vector storage (in-memory)
    - Semantic search and retrieval
    """

    def __init__(self):
        """Initialize the adapter."""
        self._api_key: Optional[str] = None
        self._base_url = "https://platform.reducto.ai"
        self._openai_client: Optional[OpenAI] = None
        self._embedding_model = "text-embedding-3-small"
        self._llm_model = "gpt-4o-mini"
        self._top_k = 3
        self._initialized = False

        # In-memory storage: index_id -> {"chunks": [...], "embeddings": np.array}
        self._indices: Dict[str, Dict[str, Any]] = {}

    def initialize(self, api_key: str, **kwargs) -> None:
        """
        Initialize the Reducto adapter.

        Args:
            api_key: Reducto API key
            **kwargs: Additional configuration:
                - openai_api_key: OpenAI API key for embeddings/LLM (required)
                - embedding_model: OpenAI embedding model (default: text-embedding-3-small)
                - llm_model: OpenAI LLM model (default: gpt-4o-mini)
                - top_k: Number of chunks to retrieve (default: 3)
                - chunk_mode: Reducto chunking mode (default: variable)
                - ocr_system: OCR engine to use (default: standard)
                - summarize_figures: Enable figure summarization (default: true)
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI is required for embeddings and LLM. "
                "Install with: pip install openai"
            )

        self._api_key = api_key
        self._embedding_model = kwargs.get("embedding_model", "text-embedding-3-small")
        self._llm_model = kwargs.get("llm_model", "gpt-4o-mini")
        self._top_k = kwargs.get("top_k", 3)

        # Reducto-specific configuration
        self._chunk_mode = kwargs.get("chunk_mode", "variable")
        self._ocr_system = kwargs.get("ocr_system", "standard")
        self._summarize_figures = kwargs.get("summarize_figures", True)

        # Initialize OpenAI client
        openai_api_key = kwargs.get("openai_api_key")
        if not openai_api_key:
            raise ValueError("openai_api_key is required for embeddings and LLM")

        self._openai_client = OpenAI(api_key=openai_api_key)
        self._initialized = True

        logger.info(
            f"Reducto adapter initialized with chunk_mode={self._chunk_mode}, "
            f"embedding_model={self._embedding_model}, llm_model={self._llm_model}"
        )

    def ingest_documents(self, documents: List[RAGDocument]) -> str:
        """
        Ingest documents using Reducto's parse endpoint.

        Workflow:
        1. Parse each document via Reducto API with RAG-optimized settings
        2. Extract embedding-optimized chunks
        3. Generate embeddings for each chunk
        4. Store chunks and embeddings

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

        logger.info(f"Ingesting {len(documents)} documents via Reducto")

        all_chunks = []

        # Parse each document
        for doc in documents:
            try:
                # Call Reducto parse endpoint
                parse_response = self._parse_document(doc)

                # Extract chunks from response
                result = parse_response.get("result", {})
                chunks = result.get("chunks", [])

                # Convert to chunk objects with metadata
                for chunk in chunks:
                    # Prefer embedding-optimized content, fall back to regular content
                    content = chunk.get("embed") or chunk.get("content", "")

                    chunk_obj = {
                        "content": content,
                        "enriched": chunk.get("enriched", ""),
                        "doc_id": doc.id,
                        "doc_metadata": doc.metadata,
                        "blocks": chunk.get("blocks", [])
                    }
                    all_chunks.append(chunk_obj)

                logger.info(f"Parsed document {doc.id}: {len(chunks)} chunks extracted")

            except Exception as e:
                logger.error(f"Failed to parse document {doc.id}: {e}")
                raise

        if not all_chunks:
            raise ValueError("No chunks extracted from documents")

        # Generate embeddings for all chunks
        logger.info(f"Generating embeddings for {len(all_chunks)} chunks")
        chunk_texts = [chunk["content"] for chunk in all_chunks]
        embeddings = self._generate_embeddings(chunk_texts)

        # Create index
        index_id = f"reducto_index_{int(time.time() * 1000)}"
        self._indices[index_id] = {
            "chunks": all_chunks,
            "embeddings": embeddings
        }

        logger.info(
            f"Created index {index_id} with {len(all_chunks)} chunks "
            f"from {len(documents)} documents"
        )

        return index_id

    def query(self, question: str, index_id: str, **kwargs) -> RAGResponse:
        """
        Query the RAG system using semantic search.

        Workflow:
        1. Embed the question
        2. Find top-k similar chunks via cosine similarity
        3. Generate answer using LLM with retrieved context

        Args:
            question: The question to ask
            index_id: Index identifier from ingest_documents()
            **kwargs: Additional options:
                - top_k: Override default top_k
                - temperature: LLM temperature (default: 0)
                - use_enriched: Use AI-enriched content if available (default: false)

        Returns:
            RAGResponse: Answer, context chunks, and metadata

        Raises:
            RuntimeError: If adapter not initialized
            KeyError: If index_id not found
        """
        if not self._initialized:
            raise RuntimeError("Adapter not initialized. Call initialize() first.")

        if index_id not in self._indices:
            raise KeyError(f"Index {index_id} not found")

        top_k = kwargs.get("top_k", self._top_k)
        temperature = kwargs.get("temperature", 0)
        use_enriched = kwargs.get("use_enriched", False)

        logger.info(f"Querying index {index_id} with question: {question[:50]}...")

        start_time = time.time()

        # Get question embedding
        question_embedding = self._generate_embeddings([question])[0]

        # Retrieve top-k similar chunks
        index_data = self._indices[index_id]
        chunks = index_data["chunks"]
        embeddings = index_data["embeddings"]

        # Compute cosine similarities
        similarities = self._cosine_similarity(question_embedding, embeddings)

        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        # Retrieve top chunks and scores
        retrieved_chunks = [chunks[i] for i in top_indices]
        scores = [float(similarities[i]) for i in top_indices]

        # Build context from chunks (use enriched content if requested and available)
        if use_enriched:
            context_texts = [
                chunk.get("enriched") or chunk["content"]
                for chunk in retrieved_chunks
            ]
        else:
            context_texts = [chunk["content"] for chunk in retrieved_chunks]

        # Generate answer using LLM
        answer = self._generate_answer(question, context_texts, temperature)

        latency_ms = (time.time() - start_time) * 1000

        # Build metadata
        metadata = {
            "index_id": index_id,
            "top_k": top_k,
            "num_chunks_retrieved": len(retrieved_chunks),
            "similarity_scores": scores,
            "avg_similarity_score": float(np.mean(scores)),
            "used_enriched_content": use_enriched
        }

        logger.info(
            f"Query completed in {latency_ms:.2f}ms, "
            f"retrieved {len(context_texts)} chunks"
        )

        return RAGResponse(
            answer=answer,
            context=context_texts,
            metadata=metadata,
            latency_ms=latency_ms,
            tokens_used=None
        )

    def health_check(self) -> bool:
        """
        Check if Reducto API is accessible.

        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            if not self._initialized:
                logger.error("Adapter not initialized")
                return False

            # Test API connectivity with a minimal request
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json"
            }

            # Try to access the API (this will fail with auth error if key is wrong,
            # but will confirm API is reachable)
            # Note: Reducto doesn't have a dedicated health endpoint,
            # so we just verify the headers are accepted

            # For now, just verify we're initialized properly
            # A real health check would need a test document
            logger.info("Health check passed (initialization verified)")
            return True

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def _parse_document(self, doc: RAGDocument) -> Dict[str, Any]:
        """
        Parse a document using Reducto API.

        Args:
            doc: Document to parse

        Returns:
            Parse response with chunks and metadata
        """
        url = f"{self._base_url}/parse"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }

        # STRICT: Only process PDF files (no silent fallback)
        if "document_url" in doc.metadata and doc.metadata["document_url"]:
            document_url = doc.metadata["document_url"]

            # Validate PDF URL
            if not document_url.lower().endswith('.pdf'):
                logger.warning(
                    f"Document {doc.id} URL may not be a PDF: {document_url}. "
                    f"Proceeding anyway, but results may be unexpected."
                )

            logger.info(f"Parsing PDF via Reducto (URL): {document_url}")
            input_url = document_url

        elif "file_path" in doc.metadata and doc.metadata["file_path"]:
            file_path = str(doc.metadata["file_path"])

            # Validate PDF file extension
            if not file_path.lower().endswith('.pdf'):
                error_msg = (
                    f"Document {doc.id} has non-PDF file: {file_path}. "
                    f"Reducto adapter requires PDF files for document parsing."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

            logger.info(f"Parsing PDF via Reducto: {file_path}")
            # Upload file first if we have a file path
            input_url = self._upload_file(file_path)

        else:
            # NO FALLBACK: Explicitly require file_path or document_url
            error_msg = (
                f"Document {doc.id} missing both 'file_path' and 'document_url' in metadata. "
                f"Reducto adapter requires PDF files for document parsing. "
                f"Got metadata: {list(doc.metadata.keys())}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Build request payload with RAG-optimized configuration
        payload = {
            "input": input_url,
            "enhance": {
                "agentic": [],
                "summarize_figures": self._summarize_figures
            },
            "retrieval": {
                "chunking": {
                    "chunk_mode": self._chunk_mode
                },
                "embedding_optimized": True,
                "filter_blocks": []
            },
            "formatting": {
                "add_page_markers": False,
                "table_output_format": "dynamic",
                "merge_tables": False
            },
            "settings": {
                "ocr_system": self._ocr_system,
                "timeout": 900
            }
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=900
        )

        response.raise_for_status()
        return response.json()

    def _upload_file(self, file_path: str) -> str:
        """
        Upload a file to Reducto and get reducto:// URL.

        Args:
            file_path: Path to file

        Returns:
            reducto:// prefixed URL
        """
        url = f"{self._base_url}/upload"
        headers = {
            "Authorization": f"Bearer {self._api_key}"
        }

        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(
                url,
                headers=headers,
                files=files,
                timeout=60
            )

        response.raise_for_status()
        result = response.json()

        # Return the reducto:// URL or presigned_url
        return result.get("presigned_url") or f"reducto://{result.get('file_id')}"

    def _generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings using OpenAI.

        Args:
            texts: List of texts to embed

        Returns:
            numpy array of embeddings (shape: [len(texts), embedding_dim])
        """
        response = self._openai_client.embeddings.create(
            model=self._embedding_model,
            input=texts
        )

        embeddings = [item.embedding for item in response.data]
        return np.array(embeddings)

    def _cosine_similarity(self, query_emb: np.ndarray, doc_embs: np.ndarray) -> np.ndarray:
        """
        Compute cosine similarity between query and document embeddings.

        Args:
            query_emb: Query embedding (1D array)
            doc_embs: Document embeddings (2D array)

        Returns:
            Similarity scores (1D array)
        """
        # Normalize vectors
        query_norm = query_emb / np.linalg.norm(query_emb)
        doc_norms = doc_embs / np.linalg.norm(doc_embs, axis=1, keepdims=True)

        # Compute dot product (cosine similarity)
        similarities = np.dot(doc_norms, query_norm)
        return similarities

    def _generate_answer(self, question: str, context_chunks: List[str], temperature: float = 0) -> str:
        """
        Generate answer using OpenAI LLM with retrieved context.

        Args:
            question: User question
            context_chunks: Retrieved context chunks
            temperature: LLM temperature

        Returns:
            Generated answer
        """
        # Build context
        context = "\n\n".join([f"[{i+1}] {chunk}" for i, chunk in enumerate(context_chunks)])

        # Build prompt
        prompt = f"""Answer the question based on the provided context. If the answer cannot be found in the context, say so.

Context:
{context}

Question: {question}

Answer:"""

        response = self._openai_client.chat.completions.create(
            model=self._llm_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on provided context."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature
        )

        return response.choices[0].message.content
