"""Test PolicyQA dataset loader."""

import pytest
from src.datasets.loader import DatasetLoader


def test_policyqa_load_minimal():
    """Test loading a minimal sample of PolicyQA dataset (10 samples for speed)."""
    dataset = DatasetLoader.load_policyqa(
        split='train',
        max_samples=10
    )

    # Verify dataset structure
    assert dataset.dataset_name == 'PolicyQA'
    assert len(dataset) > 0, "Should have samples"
    assert len(dataset) <= 10, "Should respect max_samples limit"

    # Verify sample structure
    sample = dataset.samples[0]
    assert sample.question, "Question should not be empty"
    assert sample.context, "Context (privacy policy text) should not be empty"
    assert sample.ground_truth, "Ground truth answer should not be empty"

    # Verify metadata (minimal per user preference)
    assert 'question_id' in sample.metadata
    assert 'website_title' in sample.metadata
    assert 'paragraph_index' in sample.metadata

    # Context should be reasonable length (privacy policy paragraph)
    assert len(sample.context) > 100, \
        "Privacy policy context should be substantial (>100 chars)"

    print(f"\n✓ Test passed: {len(dataset)} samples from PolicyQA")
    print(f"  Total questions: {dataset.metadata['total_questions']}")
    print(f"  Samples created: {dataset.metadata['samples_created']}")
    print(f"  Websites: {dataset.metadata['total_websites']}")


def test_policyqa_all_splits():
    """Test that all PolicyQA splits (train, dev, test) can be loaded."""
    splits = ['train', 'dev', 'test']

    for split in splits:
        dataset = DatasetLoader.load_policyqa(split=split, max_samples=5)
        assert len(dataset) > 0, f"{split} split should have samples"
        assert dataset.metadata['split'] == split
        print(f"✓ {split} split loaded: {len(dataset)} samples")


def test_policyqa_sample_content():
    """Test that PolicyQA samples have reasonable privacy policy content."""
    dataset = DatasetLoader.load_policyqa(split='dev', max_samples=5)

    if len(dataset) == 0:
        pytest.skip("No samples available (download may have failed)")

    sample = dataset.samples[0]

    # Question should be a proper sentence
    assert len(sample.question.split()) >= 3, "Question should have multiple words"

    # Context should contain privacy policy language indicators
    context_lower = sample.context.lower()
    # Check for common privacy policy terms (at least one should be present)
    privacy_indicators = [
        'privacy', 'information', 'data', 'collect', 'personal',
        'policy', 'user', 'service', 'share', 'security'
    ]
    has_indicator = any(indicator in context_lower for indicator in privacy_indicators)
    assert has_indicator, "Context should contain privacy policy language"

    # Ground truth should be non-trivial
    assert len(sample.ground_truth.split()) >= 2, "Answer should have at least 2 words"

    # Website title should be present
    assert sample.metadata['website_title'], "Should have website title"

    print(f"\n✓ Sample content validation passed")
    print(f"  Website: {sample.metadata['website_title']}")
    print(f"  Question: {sample.question[:100]}...")
    print(f"  Answer: {sample.ground_truth[:100]}...")
    print(f"  Context length: {len(sample.context)} chars")


def test_policyqa_extractive_answers():
    """Test that PolicyQA answers are extractive (present in context)."""
    dataset = DatasetLoader.load_policyqa(split='dev', max_samples=3)

    if len(dataset) == 0:
        pytest.skip("No samples available")

    # Check that at least some answers are found in context
    found_count = 0
    for sample in dataset.samples:
        if sample.ground_truth.lower() in sample.context.lower():
            found_count += 1

    # At least 50% of answers should be found in context (some may differ due to preprocessing)
    assert found_count >= len(dataset) * 0.5, \
        "Most answers should be extractive (found in context)"

    print(f"✓ Extractive answer check: {found_count}/{len(dataset)} answers found in context")


if __name__ == "__main__":
    # Run tests manually
    print("Testing PolicyQA loader...")
    test_policyqa_load_minimal()
    test_policyqa_all_splits()
    test_policyqa_sample_content()
    test_policyqa_extractive_answers()
    print("\n✅ All PolicyQA tests passed!")
