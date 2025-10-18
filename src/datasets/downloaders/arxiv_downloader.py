"""
Arxiv PDF downloader with caching and rate limiting.

Downloads research documents from arxiv.org for RAG evaluation datasets.
"""

import time
import arxiv
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ArxivDownloader:
    """
    Download PDFs from arxiv.org with caching and rate limiting.

    Features:
    - Caches downloaded PDFs locally
    - Rate limiting to respect arxiv API
    - Graceful error handling (returns None on failure)
    """

    def __init__(
        self,
        cache_dir: str = "data/datasets/Qasper/pdfs",
        rate_limit_delay: float = 3.0
    ):
        """
        Initialize arxiv downloader.

        Args:
            cache_dir: Directory to cache downloaded PDFs
            rate_limit_delay: Delay between downloads in seconds (arxiv recommends 3s)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.rate_limit_delay = rate_limit_delay
        self.last_download_time = 0

    def _rate_limit(self):
        """Apply rate limiting between downloads."""
        elapsed = time.time() - self.last_download_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_download_time = time.time()

    def download(self, arxiv_id: str) -> Optional[Path]:
        """
        Download PDF for given arxiv ID.

        Args:
            arxiv_id: Arxiv document ID (e.g., "1909.00694")

        Returns:
            Path to downloaded PDF, or None if download failed
        """
        # Check cache first
        pdf_path = self.cache_dir / f"{arxiv_id}.pdf"
        if pdf_path.exists():
            logger.debug(f"Using cached PDF: {arxiv_id}")
            return pdf_path

        # Apply rate limiting
        self._rate_limit()

        try:
            # Search for document
            logger.info(f"Downloading arxiv document: {arxiv_id}")
            search = arxiv.Search(id_list=[arxiv_id])
            result = next(search.results())

            # Download PDF
            result.download_pdf(dirpath=str(self.cache_dir), filename=f"{arxiv_id}.pdf")

            logger.info(f"Successfully downloaded: {arxiv_id}")
            return pdf_path

        except StopIteration:
            logger.warning(f"Document not found on arxiv: {arxiv_id}")
            return None
        except Exception as e:
            logger.warning(f"Failed to download {arxiv_id}: {e}")
            return None

    def download_batch(self, arxiv_ids: list[str]) -> dict[str, Optional[Path]]:
        """
        Download multiple PDFs.

        Args:
            arxiv_ids: List of arxiv document IDs

        Returns:
            Dict mapping arxiv_id -> pdf_path (or None if failed)
        """
        results = {}
        for arxiv_id in arxiv_ids:
            results[arxiv_id] = self.download(arxiv_id)
        return results
