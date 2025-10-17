"""
Demo: Loading SQuAD dataset and preparing for Ragas evaluation.

This script demonstrates:
1. Loading SQuAD 2.0 dataset using DatasetLoader
2. Extracting questions, contexts, and ground truth answers
3. Converting to Ragas evaluation format
"""

from pathlib import Path
from src.datasets.loader import DatasetLoader

# Path to test dataset
PROJECT_ROOT = Path(__file__).parent.parent
MINI_SQUAD_PATH = PROJECT_ROOT / "data" / "test" / "mini_squad.json"


def main():
    print("=" * 60)
    print("RAGRace Dataset Loading Demo")
    print("=" * 60)
    print()

    # Load dataset
    print("1. Loading mini_squad.json...")
    dataset = DatasetLoader.load_squad(str(MINI_SQUAD_PATH))

    print(f"   ✓ Loaded {len(dataset)} samples")
    print(f"   ✓ Dataset: {dataset.dataset_name}")
    print(f"   ✓ Version: {dataset.metadata['version']}")
    print()

    # Show first sample
    print("2. First sample structure:")
    sample = dataset.samples[0]
    print(f"   Question: {sample.question}")
    print(f"   Ground Truth: {sample.ground_truth}")
    print(f"   Context (first 100 chars): {sample.context[:100]}...")
    print(f"   Question ID: {sample.metadata['question_id']}")
    print(f"   Article: {sample.metadata['article_title']}")
    print()

    # Convert to Ragas format
    print("3. Converting to Ragas format...")
    ragas_data = dataset.to_ragas_format()
    print(f"   ✓ Converted {len(ragas_data)} samples")
    print()
    print("   First sample in Ragas format:")
    print(f"   - user_input: {ragas_data[0]['user_input']}")
    print(f"   - reference: {ragas_data[0]['reference']}")
    print()

    # Show all questions
    print("4. All questions in dataset:")
    for i, sample in enumerate(dataset.samples, 1):
        print(f"   Q{i}: {sample.question}")
    print()

    print("=" * 60)
    print("Next steps:")
    print("- Implement a RAG provider adapter")
    print("- Run questions through RAG system")
    print("- Use RagasEvaluator to score responses")
    print("=" * 60)


if __name__ == "__main__":
    main()
