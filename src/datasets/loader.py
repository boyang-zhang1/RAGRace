"""
Generic dataset loader with preprocessor routing.

Loads datasets and applies appropriate preprocessor based on dataset type.
"""

from typing import Dict, Any, Optional
from pathlib import Path
from .preprocessors.base import BasePreprocessor, ProcessedDataset
from .preprocessors.squad import SquadPreprocessor
from .preprocessors.qasper_preprocessor import QasperPreprocessor
from .preprocessors.policyqa_preprocessor import PolicyQAPreprocessor


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
        'qasper': QasperPreprocessor,
        'policyqa': PolicyQAPreprocessor,
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

    def load(self, file_path: Optional[str] = None, **kwargs) -> ProcessedDataset:
        """
        Load and preprocess dataset file.

        Args:
            file_path: Path to dataset file (None for datasets loaded from API)
            **kwargs: Preprocessor-specific options
                For SQuAD:
                    - filter_impossible: bool = True
                    - max_samples: int = None
                For Qasper:
                    - split: str = 'train'
                    - max_docs: int = None
                    - filter_unanswerable: bool = True
                For PolicyQA:
                    - split: str = 'train'
                    - max_samples: int = None

        Returns:
            ProcessedDataset with standardized samples

        Raises:
            FileNotFoundError: If file_path is required but does not exist
        """
        # Some datasets (like Qasper) load from API and don't need file_path
        if file_path is not None:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"Dataset file not found: {file_path}")
            file_path_str = str(path)
        else:
            file_path_str = None

        # Delegate to appropriate preprocessor
        processed = self.preprocessor.process(file_path_str, **kwargs)

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

    @staticmethod
    def load_qasper(split: str = "train", **kwargs) -> ProcessedDataset:
        """
        Convenience method to load Qasper dataset.

        Args:
            split: Dataset split ('train', 'validation', 'test')
            **kwargs: Qasper preprocessor options
                - max_docs: int = None (None = all docs, or set limit for testing)
                - filter_unanswerable: bool = True

        Returns:
            ProcessedDataset with Qasper samples (questions + raw PDF text)

        Example:
            # Load all documents from train split
            dataset = DatasetLoader.load_qasper(split='train')

            # Load first 10 documents for quick testing
            dataset = DatasetLoader.load_qasper(split='train', max_docs=10)
        """
        loader = DatasetLoader('qasper')
        return loader.load(file_path=None, split=split, **kwargs)

    @staticmethod
    def load_policyqa(split: str = "train", **kwargs) -> ProcessedDataset:
        """
        Convenience method to load PolicyQA dataset.

        Args:
            split: Dataset split ('train', 'dev', 'test')
            **kwargs: PolicyQA preprocessor options
                - max_samples: int = None (None = all samples, or set limit for testing)

        Returns:
            ProcessedDataset with PolicyQA samples (privacy policy QA)

        Example:
            # Load all samples from train split
            dataset = DatasetLoader.load_policyqa(split='train')

            # Load first 10 samples for quick testing
            dataset = DatasetLoader.load_policyqa(split='train', max_samples=10)
        """
        loader = DatasetLoader('policyqa')
        return loader.load(file_path=None, split=split, **kwargs)
