"""
Tests for SQuAD dataset loader and preprocessor.
"""

import pytest
from pathlib import Path
from src.datasets.loader import DatasetLoader
from src.datasets.preprocessors.squad import SquadPreprocessor


# Path to test dataset
TEST_DATA_DIR = Path(__file__).parent.parent / "data" / "test"
MINI_SQUAD_PATH = TEST_DATA_DIR / "mini_squad.json"


class TestSquadPreprocessor:
    """Tests for SquadPreprocessor."""

    def test_process_mini_squad(self):
        """Test processing mini_squad.json with 2 questions max."""
        preprocessor = SquadPreprocessor()
        result = preprocessor.process(str(MINI_SQUAD_PATH), max_samples=2)

        # Check basic structure
        assert result.dataset_name == 'SQuAD2'
        assert len(result.samples) <= 2
        assert result.metadata['version'] == 'v2.0'

        # Check first sample
        sample = result.samples[0]
        assert sample.question == "When did Beyonce start becoming popular?"
        assert "in the late 1990s" in sample.ground_truth
        assert len(sample.context) > 0
        assert sample.metadata['article_title'] == 'Beyoncé'
        assert sample.metadata['is_impossible'] is False

    def test_filter_impossible_questions(self):
        """Test that impossible questions are filtered by default."""
        preprocessor = SquadPreprocessor()
        result = preprocessor.process(str(MINI_SQUAD_PATH), filter_impossible=True, max_samples=2)

        # All samples should have is_impossible=False
        for sample in result.samples:
            assert sample.metadata['is_impossible'] is False

    def test_max_samples_limit(self):
        """Test max_samples parameter limits output."""
        preprocessor = SquadPreprocessor()
        result = preprocessor.process(str(MINI_SQUAD_PATH), max_samples=2)

        assert len(result.samples) == 2

    def test_ragas_format_conversion(self):
        """Test conversion to Ragas EvaluationDataset format."""
        preprocessor = SquadPreprocessor()
        result = preprocessor.process(str(MINI_SQUAD_PATH), max_samples=2)

        ragas_data = result.to_ragas_format()

        assert len(ragas_data) <= 2
        assert 'user_input' in ragas_data[0]
        assert 'reference' in ragas_data[0]
        assert ragas_data[0]['user_input'] == "When did Beyonce start becoming popular?"


class TestDatasetLoader:
    """Tests for DatasetLoader."""

    def test_load_squad_via_loader(self):
        """Test loading SQuAD dataset via generic loader."""
        loader = DatasetLoader('squad')
        result = loader.load(str(MINI_SQUAD_PATH), max_samples=2)

        assert len(result.samples) <= 2
        assert result.dataset_name == 'SQuAD2'

    def test_load_squad_convenience_method(self):
        """Test convenience method for loading SQuAD."""
        result = DatasetLoader.load_squad(str(MINI_SQUAD_PATH), max_samples=2)

        assert len(result.samples) <= 2
        assert result.dataset_name == 'SQuAD2'

    def test_unsupported_dataset_type(self):
        """Test that unsupported dataset types raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported dataset type"):
            DatasetLoader('unsupported_type')

    def test_file_not_found(self):
        """Test that missing file raises FileNotFoundError."""
        loader = DatasetLoader('squad')
        with pytest.raises(FileNotFoundError):
            loader.load('/nonexistent/path/to/file.json')


class TestDatasetSampleStructure:
    """Tests for DatasetSample structure and metadata."""

    def test_sample_has_all_required_fields(self):
        """Test that each sample has required fields."""
        result = DatasetLoader.load_squad(str(MINI_SQUAD_PATH), max_samples=2)

        for sample in result.samples:
            assert hasattr(sample, 'question')
            assert hasattr(sample, 'context')
            assert hasattr(sample, 'ground_truth')
            assert hasattr(sample, 'metadata')

            # Check metadata contents
            assert 'question_id' in sample.metadata
            assert 'article_title' in sample.metadata
            assert 'is_impossible' in sample.metadata

    def test_ground_truth_extraction(self):
        """Test that ground truth answers are correctly extracted."""
        result = DatasetLoader.load_squad(str(MINI_SQUAD_PATH), max_samples=2)

        # First question should have "in the late 1990s" as answer
        assert "in the late 1990s" in result.samples[0].ground_truth

    def test_context_is_not_empty(self):
        """Test that context is populated."""
        result = DatasetLoader.load_squad(str(MINI_SQUAD_PATH), max_samples=2)

        for sample in result.samples:
            assert len(sample.context) > 0
            assert isinstance(sample.context, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
