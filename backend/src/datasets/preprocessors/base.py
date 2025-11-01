"""
Base preprocessor interface for datasets.

All dataset preprocessors must implement this interface to ensure
standardized output format compatible with Ragas evaluation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class DatasetSample:
    """
    Standardized dataset sample format.

    Compatible with Ragas EvaluationDataset format:
    - question: The query (maps to 'user_input' in Ragas)
    - context: The document/passage (maps to 'retrieved_contexts' in Ragas)
    - ground_truth: The expected answer (maps to 'reference' in Ragas)
    - metadata: Additional information (question_id, is_impossible, etc.)
    """
    question: str
    context: str
    ground_truth: str
    metadata: Dict[str, Any]


@dataclass
class ProcessedDataset:
    """Container for processed dataset samples."""
    samples: List[DatasetSample]
    dataset_name: str
    metadata: Dict[str, Any]

    def __len__(self) -> int:
        return len(self.samples)

    def to_ragas_format(self) -> List[Dict[str, Any]]:
        """
        Convert to Ragas EvaluationDataset format.

        Returns:
            List of dicts with keys: user_input, reference, retrieved_contexts (optional)
        """
        return [
            {
                "user_input": sample.question,
                "reference": sample.ground_truth,
                # Note: retrieved_contexts and response will be added after RAG system runs
                "metadata": sample.metadata
            }
            for sample in self.samples
        ]


class BasePreprocessor(ABC):
    """
    Base preprocessor interface for all dataset types.

    Subclasses must implement process() to convert raw dataset
    into standardized DatasetSample format.
    """

    @abstractmethod
    def process(self, file_path: str, **kwargs) -> ProcessedDataset:
        """
        Process raw dataset file into standardized format.

        Args:
            file_path: Path to the dataset file
            **kwargs: Dataset-specific processing options

        Returns:
            ProcessedDataset containing standardized samples
        """
        pass
