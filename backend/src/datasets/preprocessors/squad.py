"""
SQuAD 2.0 dataset preprocessor.

Parses SQuAD 2.0 JSON format and extracts question-context-answer triples
in standardized format for RAG evaluation.
"""

import json
from typing import Dict, Any
from .base import BasePreprocessor, DatasetSample, ProcessedDataset


class SquadPreprocessor(BasePreprocessor):
    """
    Preprocessor for SQuAD 2.0 dataset.

    SQuAD 2.0 structure:
    {
        "version": "v2.0",
        "data": [
            {
                "title": "Article title",
                "paragraphs": [
                    {
                        "context": "The paragraph text...",
                        "qas": [
                            {
                                "question": "Question text?",
                                "id": "unique_id",
                                "answers": [{"text": "answer", "answer_start": 123}],
                                "is_impossible": false
                            }
                        ]
                    }
                ]
            }
        ]
    }
    """

    def process(
        self,
        file_path: str,
        filter_impossible: bool = True,
        max_samples: int = None
    ) -> ProcessedDataset:
        """
        Process SQuAD 2.0 JSON file.

        Args:
            file_path: Path to SQuAD 2.0 JSON file
            filter_impossible: If True, skip questions marked as impossible
            max_samples: Maximum number of samples to extract (None = all)

        Returns:
            ProcessedDataset with standardized samples
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        samples = []
        total_articles = len(data['data'])
        total_paragraphs = 0
        total_questions = 0
        skipped_impossible = 0

        for article in data['data']:
            title = article['title']

            for paragraph in article['paragraphs']:
                context = paragraph['context']
                total_paragraphs += 1

                for qa in paragraph['qas']:
                    total_questions += 1

                    # Skip impossible questions if requested
                    if filter_impossible and qa.get('is_impossible', False):
                        skipped_impossible += 1
                        continue

                    # Extract ground truth answer
                    # For impossible questions, ground_truth is empty
                    if qa.get('is_impossible', False):
                        ground_truth = ""
                    elif qa['answers']:
                        # Use first answer as ground truth
                        ground_truth = qa['answers'][0]['text']
                    else:
                        ground_truth = ""

                    # Create standardized sample
                    sample = DatasetSample(
                        question=qa['question'],
                        context=context,
                        ground_truth=ground_truth,
                        metadata={
                            'question_id': qa['id'],
                            'article_title': title,
                            'is_impossible': qa.get('is_impossible', False),
                            'all_answers': [ans['text'] for ans in qa.get('answers', [])],
                            'answer_starts': [ans['answer_start'] for ans in qa.get('answers', [])]
                        }
                    )
                    samples.append(sample)

                    # Check max_samples limit
                    if max_samples and len(samples) >= max_samples:
                        break

                if max_samples and len(samples) >= max_samples:
                    break

            if max_samples and len(samples) >= max_samples:
                break

        # Create processed dataset with metadata
        dataset_metadata = {
            'version': data.get('version', 'unknown'),
            'total_articles': total_articles,
            'total_paragraphs': total_paragraphs,
            'total_questions': total_questions,
            'skipped_impossible': skipped_impossible,
            'filter_impossible': filter_impossible,
            'samples_extracted': len(samples)
        }

        return ProcessedDataset(
            samples=samples,
            dataset_name='SQuAD2',
            metadata=dataset_metadata
        )
