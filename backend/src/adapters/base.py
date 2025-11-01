"""
Base adapter interface for RAG providers.

All RAG provider adapters MUST implement this interface to ensure
standardized input/output across different providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class Document:
    """Standardized document format for RAG ingestion."""
    id: str
    content: str
    metadata: Dict[str, Any]


@dataclass
class RAGResponse:
    """Standardized response format from RAG queries."""
    answer: str
    context: List[str]  # Retrieved context chunks
    metadata: Dict[str, Any]  # Provider-specific metadata
    latency_ms: float
    tokens_used: Optional[int] = None


class BaseAdapter(ABC):
    """
    Base adapter interface that all RAG providers must implement.

    This ensures all providers have a standardized interface for:
    - Authentication
    - Document ingestion
    - Query execution
    - Health checks
    """

    @abstractmethod
    def initialize(self, api_key: str, **kwargs) -> None:
        """
        Initialize the RAG provider connection.

        Args:
            api_key: API key for authentication
            **kwargs: Provider-specific configuration
        """
        pass

    @abstractmethod
    def ingest_documents(self, documents: List[Document]) -> str:
        """
        Upload documents to RAG system.

        Args:
            documents: List of documents to ingest

        Returns:
            index_id: Identifier for the created index
        """
        pass

    @abstractmethod
    def query(self, question: str, index_id: str, **kwargs) -> RAGResponse:
        """
        Query the RAG system.

        Args:
            question: The question to ask
            index_id: The index to query against
            **kwargs: Provider-specific query parameters

        Returns:
            RAGResponse: Standardized response object
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the provider is accessible.

        Returns:
            bool: True if provider is healthy, False otherwise
        """
        pass
