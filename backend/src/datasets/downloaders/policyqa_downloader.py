"""
PolicyQA dataset downloader with caching.

Downloads PolicyQA JSON files from GitHub repository.
"""

import requests
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class PolicyQADownloader:
    """
    Download PolicyQA JSON files from GitHub with caching.

    Features:
    - Caches downloaded JSON files locally
    - Downloads train.json, dev.json, test.json from GitHub
    - No rate limiting needed (GitHub CDN is fast)
    """

    # GitHub raw content URLs
    BASE_URL = "https://raw.githubusercontent.com/wasiahmad/PolicyQA/main/data"
    VALID_SPLITS = ['train', 'dev', 'test']

    def __init__(self, cache_dir: str = "data/datasets/PolicyQA"):
        """
        Initialize PolicyQA downloader.

        Args:
            cache_dir: Directory to cache downloaded JSON files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def download(self, split: str = "train") -> Optional[Path]:
        """
        Download PolicyQA JSON file for given split.

        Args:
            split: Dataset split ('train', 'dev', or 'test')

        Returns:
            Path to downloaded JSON file, or None if download failed

        Raises:
            ValueError: If split is not valid
        """
        if split not in self.VALID_SPLITS:
            raise ValueError(
                f"Invalid split: {split}. Must be one of {self.VALID_SPLITS}"
            )

        # Check cache first
        json_path = self.cache_dir / f"{split}.json"
        if json_path.exists():
            logger.debug(f"Using cached PolicyQA file: {split}.json")
            return json_path

        # Download from GitHub
        url = f"{self.BASE_URL}/{split}.json"
        logger.info(f"Downloading PolicyQA {split} split from {url}")

        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            # Write to cache
            with open(json_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            file_size_mb = json_path.stat().st_size / (1024 * 1024)
            logger.info(f"Successfully downloaded: {split}.json ({file_size_mb:.2f} MB)")
            return json_path

        except requests.RequestException as e:
            logger.error(f"Failed to download {split}.json: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading {split}.json: {e}")
            return None

    def download_all_splits(self) -> dict[str, Optional[Path]]:
        """
        Download all PolicyQA splits (train, dev, test).

        Returns:
            Dict mapping split_name -> json_path (or None if failed)
        """
        results = {}
        for split in self.VALID_SPLITS:
            results[split] = self.download(split)
        return results
