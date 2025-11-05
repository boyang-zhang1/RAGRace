"""Base adapter interface for PDF parsing."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class PageResult:
    """Result for a single page of parsed content."""

    page_number: int
    markdown: str
    images: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParseResult:
    """Complete parsing result from a provider."""

    provider: str
    total_pages: int
    pages: List[PageResult]
    raw_response: Dict[str, Any]
    processing_time: float
    usage: Dict[str, Any] = field(default_factory=dict)  # Credits, model info, etc.


class BaseParseAdapter(ABC):
    """Abstract base class for PDF parsing adapters."""

    @abstractmethod
    async def parse_pdf(self, pdf_path: Path) -> ParseResult:
        """
        Parse a PDF file and return structured results.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            ParseResult containing page-by-page markdown and metadata
        """
        pass
