"""
LLM-based scoring engine using GPT structured outputs.

Compares RAG predictions against ground truth using batch evaluation
for fairness and efficiency.
"""

import os
from typing import List, Dict
from pydantic import BaseModel
from openai import OpenAI


class ProviderScore(BaseModel):
    """Score for a single provider's prediction."""
    provider: str
    semantic_score: int  # 0-100


class BatchScoreResponse(BaseModel):
    """Structured response containing all provider scores."""
    scores: List[ProviderScore]


class Scorer:
    """
    LLM-based scorer using GPT structured outputs.

    Evaluates all RAG providers' predictions in a SINGLE prompt for:
    1. Fairness - LLM sees all predictions together
    2. Efficiency - Saves tokens and API calls
    """

    def __init__(self, config: Dict):
        """
        Initialize scorer with configuration.

        Args:
            config: Scoring configuration from scoring.yaml
        """
        self.config = config
        api_key = os.getenv(config['api_key_env'])
        self.client = OpenAI(api_key=api_key)
        self.model = config['model']

    def score_batch(
        self,
        question: str,
        ground_truth: str,
        predictions: Dict[str, str]  # {provider_name: prediction}
    ) -> Dict[str, int]:
        """
        Score all providers' predictions in one API call.

        Args:
            question: The question asked
            ground_truth: The correct answer
            predictions: Dict mapping provider name to their prediction

        Returns:
            Dict mapping provider name to semantic score (0-100)
        """
        # Format predictions for the prompt
        predictions_text = "\n".join([
            f"{provider}: {prediction}"
            for provider, prediction in predictions.items()
        ])

        # Create simple, concise prompt
        prompt = f"""Compare each prediction to the ground truth answer.
Score semantic similarity 0-100 (0=completely wrong, 100=perfect match).

Question: {question}
Ground Truth: {ground_truth}

Predictions:
{predictions_text}

Return scores only, no explanations."""

        # Call GPT with structured output
        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise evaluator. Score predictions against ground truth."
                },
                {"role": "user", "content": prompt}
            ],
            response_format=BatchScoreResponse
        )

        # Extract scores
        result = response.choices[0].message.parsed
        return {
            score.provider: score.semantic_score
            for score in result.scores
        }

    def compute_exact_match(self, ground_truth: str, prediction: str) -> int:
        """
        Compute exact match score (0 or 1) using SQuAD-style normalization.

        Based on evaluate-v2.0.py normalization:
        - Lowercase
        - Remove articles (a, an, the)
        - Remove punctuation
        - Remove extra whitespace

        Args:
            ground_truth: The correct answer
            prediction: The predicted answer

        Returns:
            1 if exact match after normalization, 0 otherwise
        """
        import re
        import string

        def normalize(text: str) -> str:
            """Normalize text for comparison."""
            # Lowercase
            text = text.lower()
            # Remove articles
            text = re.sub(r'\b(a|an|the)\b', ' ', text)
            # Remove punctuation
            text = ''.join(ch if ch not in string.punctuation else ' ' for ch in text)
            # Remove extra whitespace
            text = ' '.join(text.split())
            return text

        return 1 if normalize(ground_truth) == normalize(prediction) else 0
