"""
LandingAI Agentic Document Extraction (ADE) RAG Provider Adapter.

Implements BaseAdapter interface for LandingAI's document parsing and extraction API.
Based on actual API documentation from https://docs.landing.ai/ade/

LandingAI ADE is a document preprocessing service - it converts unstructured documents
into structured semantic chunks. This adapter adds embedding generation and vector
search capabilities to create a complete RAG system.
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


class LandingAIAdapter(BaseAdapter):
    """
    Adapter for LandingAI Agentic Document Extraction API.

    LandingAI provides document parsing with semantic chunking.
    This adapter adds:
    - Embedding generation (via OpenAI)
    - Vector storage (in-memory)
    - Semantic search and retrieval
    """

    def __init__(self):
        """Initialize the adapter."""
        self._api_key: Optional[str] = None
        self._base_url = "https://api.va.landing.ai"
        self._openai_client: Optional[OpenAI] = None
        self._embedding_model = "text-embedding-3-small"
        self._llm_model = "gpt-4o-mini"
        self._top_k = 3
        self._initialized = False

        # In-memory storage: index_id -> {"chunks": [...], "embeddings": np.array}
        self._indices: Dict[str, Dict[str, Any]] = {}

    def initialize(self, api_key: str, **kwargs) -> None:
        """
        Initialize the LandingAI adapter.

        Args:
            api_key: LandingAI API key (VISION_AGENT_API_KEY)
            **kwargs: Additional configuration:
                - openai_api_key: OpenAI API key for embeddings/LLM
                - base_url: LandingAI base URL (default: US endpoint)
                - embedding_model: OpenAI embedding model (default: text-embedding-3-small)
                - llm_model: OpenAI LLM model (default: gpt-4o-mini)
                - top_k: Number of chunks to retrieve (default: 3)
                - model: LandingAI parse model (default: dpt-2-latest)
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI is required for embeddings and LLM. "
                "Install with: pip install openai"
            )

        self._api_key = api_key
        self._base_url = kwargs.get("base_url", "https://api.va.landing.ai")
        self._embedding_model = kwargs.get("embedding_model", "text-embedding-3-small")
        self._llm_model = kwargs.get("llm_model", "gpt-4o-mini")
        self._top_k = kwargs.get("top_k", 3)
        self._parse_model = kwargs.get("model", "dpt-2-latest")

        # Initialize OpenAI client
        openai_api_key = kwargs.get("openai_api_key")
        if not openai_api_key:
            raise ValueError("openai_api_key is required for embeddings and LLM")

        self._openai_client = OpenAI(api_key=openai_api_key)
        self._initialized = True

        logger.info(
            f"LandingAI adapter initialized with base_url={self._base_url}, "
            f"embedding_model={self._embedding_model}, llm_model={self._llm_model}"
        )

    def ingest_documents(self, documents: List[RAGDocument]) -> str:
        """
        Ingest documents using LandingAI's parse endpoint.

        Workflow:
        1. Parse each document via LandingAI ADE API
        2. Extract semantic chunks
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

        logger.info(f"Ingesting {len(documents)} documents via LandingAI")

        all_chunks = []

        # Parse each document
        for doc in documents:
            try:
                # Call LandingAI parse endpoint
                parse_response = self._parse_document(doc)

                # Extract chunks from response
                chunks = parse_response.get("chunks", [])

                # Convert to chunk objects with metadata
                for chunk in chunks:
                    chunk_obj = {
                        "content": chunk.get("markdown", ""),
                        "type": chunk.get("type", "text"),
                        "doc_id": doc.id,
                        "doc_metadata": doc.metadata,
                        "grounding": chunk.get("grounding", {}),
                        "chunk_id": chunk.get("id", "")
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
        index_id = f"landingai_index_{int(time.time() * 1000)}"
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

        # Build context from chunks
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
            "chunk_types": [chunk["type"] for chunk in retrieved_chunks]
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
        Check if LandingAI API is accessible.

        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            if not self._initialized:
                logger.error("Adapter not initialized")
                return False

            # Test API connectivity with a minimal request
            headers = {
                "Authorization": f"Bearer {self._api_key}"
            }

            # Make a simple request to check API availability
            # Using the job list endpoint as a lightweight health check
            response = requests.get(
                f"{self._base_url}/v1/ade/parse/jobs",
                headers=headers,
                timeout=5
            )

            if response.status_code in [200, 401, 403]:
                # 200: Success
                # 401/403: Auth issue but API is reachable
                logger.info("Health check passed")
                return True

            logger.error(f"Health check failed with status {response.status_code}")
            return False

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def _parse_document(self, doc: RAGDocument) -> Dict[str, Any]:
        """
        Parse a document using LandingAI ADE API.

        Args:
            doc: Document to parse

        Returns:
            Parse response with chunks and metadata
        """
        url = f"{self._base_url}/v1/ade/parse"
        headers = {
            "Authorization": f"Bearer {self._api_key}"
        }

        # STRICT: Only process PDF files (no silent fallback)
        if "file_path" in doc.metadata and doc.metadata["file_path"]:
            file_path = str(doc.metadata["file_path"])

            # Validate PDF file extension
            if not file_path.lower().endswith('.pdf'):
                error_msg = (
                    f"Document {doc.id} has non-PDF file: {file_path}. "
                    f"LandingAI adapter requires PDF files for document parsing."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

            logger.info(f"Parsing PDF via LandingAI: {file_path}")

            with open(file_path, "rb") as f:
                files = {"document": f}
                data = {"model": self._parse_model}

                response = requests.post(
                    url,
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=300
                )
        elif "document_url" in doc.metadata and doc.metadata["document_url"]:
            document_url = doc.metadata["document_url"]

            # Validate PDF URL
            if not document_url.lower().endswith('.pdf'):
                logger.warning(
                    f"Document {doc.id} URL may not be a PDF: {document_url}. "
                    f"Proceeding anyway, but results may be unexpected."
                )

            logger.info(f"Parsing PDF via LandingAI (URL): {document_url}")

            # Use URL-based parsing
            data = {
                "document_url": document_url,
                "model": self._parse_model
            }
            response = requests.post(
                url,
                headers=headers,
                data=data,
                timeout=300
            )
        else:
            # NO FALLBACK: Explicitly require file_path or document_url
            error_msg = (
                f"Document {doc.id} missing both 'file_path' and 'document_url' in metadata. "
                f"LandingAI adapter requires PDF files for document parsing. "
                f"Got metadata: {list(doc.metadata.keys())}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        response.raise_for_status()
        return response.json()

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
