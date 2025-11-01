"""
RAG Provider Adapters.

This module provides adapters for different RAG providers,
all implementing the BaseAdapter interface.
"""

from src.adapters.base import BaseAdapter, Document, RAGResponse
from src.adapters.llamaindex_adapter import LlamaIndexAdapter
from src.adapters.landingai_adapter import LandingAIAdapter
from src.adapters.reducto_adapter import ReductoAdapter

__all__ = [
    "BaseAdapter",
    "Document",
    "RAGResponse",
    "LlamaIndexAdapter",
    "LandingAIAdapter",
    "ReductoAdapter",
]
