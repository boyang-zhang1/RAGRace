"""
Generic dataset loader with preprocessor routing.

Loads datasets and applies appropriate preprocessor based on dataset type.
"""

from typing import Dict, Any, Optional
from pathlib import Path
from .preprocessors.base import BasePreprocessor, ProcessedDataset
from .preprocessors.squad import SquadPreprocessor


class DatasetLoader:
    """
    Generic dataset loader that routes to appropriate preprocessor.

    Supports:
    - SQuAD 2.0 format
    - Future: Add more dataset types as needed
    """

    # Map dataset types to their preprocessors
    PREPROCESSORS: Dict[str, type] = {
        'squad': SquadPreprocessor,
        'squad2': SquadPreprocessor,
    }

    def __init__(self, dataset_type: str):
        """
        Initialize loader with dataset type.

        Args:
            dataset_type: Type of dataset (e.g., 'squad', 'squad2')

        Raises:
            ValueError: If dataset_type is not supported
        """
        if dataset_type.lower() not in self.PREPROCESSORS:
            supported = ', '.join(self.PREPROCESSORS.keys())
            raise ValueError(
                f"Unsupported dataset type: {dataset_type}. "
                f"Supported types: {supported}"
            )

        self.dataset_type = dataset_type.lower()
        self.preprocessor: BasePreprocessor = self.PREPROCESSORS[self.dataset_type]()

    def load(self, file_path: str, **kwargs) -> ProcessedDataset:
        """
        Load and preprocess dataset file.

        Args:
            file_path: Path to dataset file
            **kwargs: Preprocessor-specific options
                For SQuAD:
                    - filter_impossible: bool = True
                    - max_samples: int = None

        Returns:
            ProcessedDataset with standardized samples

        Raises:
            FileNotFoundError: If file_path does not exist
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Dataset file not found: {file_path}")

        # Delegate to appropriate preprocessor
        processed = self.preprocessor.process(str(path), **kwargs)

        return processed

    @staticmethod
    def load_squad(file_path: str, **kwargs) -> ProcessedDataset:
        """
        Convenience method to load SQuAD dataset.

        Args:
            file_path: Path to SQuAD JSON file
            **kwargs: SQuAD preprocessor options

        Returns:
            ProcessedDataset with SQuAD samples
        """
        loader = DatasetLoader('squad')
        return loader.load(file_path, **kwargs)
