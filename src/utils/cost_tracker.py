"""
Cost tracking and analysis for RAG evaluation.

Tracks API usage and calculates costs based on provider pricing.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


# OpenAI pricing (as of Oct 2024)
# https://openai.com/api/pricing/
OPENAI_PRICING = {
    # Embedding models
    'text-embedding-3-small': {
        'input': 0.02 / 1_000_000,  # $0.02 per 1M tokens
    },
    'text-embedding-3-large': {
        'input': 0.13 / 1_000_000,  # $0.13 per 1M tokens
    },
    'text-embedding-ada-002': {
        'input': 0.10 / 1_000_000,  # $0.10 per 1M tokens
    },

    # Chat models
    'gpt-4o-mini': {
        'input': 0.150 / 1_000_000,   # $0.150 per 1M tokens
        'output': 0.600 / 1_000_000,  # $0.600 per 1M tokens
    },
    'gpt-5': {
        'input': 2.50 / 1_000_000,    # $2.50 per 1M tokens
        'output': 10.00 / 1_000_000,  # $10.00 per 1M tokens
    },
    'gpt-4': {
        'input': 30.00 / 1_000_000,   # $30.00 per 1M tokens
        'output': 60.00 / 1_000_000,  # $60.00 per 1M tokens
    },
    'gpt-3.5-turbo': {
        'input': 0.50 / 1_000_000,    # $0.50 per 1M tokens
        'output': 1.50 / 1_000_000,   # $1.50 per 1M tokens
    },
}


@dataclass
class TokenUsage:
    """Token usage for a single API call."""
    model: str
    input_tokens: int
    output_tokens: int = 0
    operation: str = "unknown"  # e.g., "embed", "chat", "evaluate"

    def cost(self) -> float:
        """Calculate cost for this usage."""
        if self.model not in OPENAI_PRICING:
            return 0.0

        pricing = OPENAI_PRICING[self.model]
        input_cost = self.input_tokens * pricing.get('input', 0)
        output_cost = self.output_tokens * pricing.get('output', 0)
        return input_cost + output_cost


@dataclass
class ProviderCost:
    """Cost breakdown for a single RAG provider."""
    provider_name: str
    embedding_tokens: int = 0
    llm_input_tokens: int = 0
    llm_output_tokens: int = 0
    num_queries: int = 0
    num_documents: int = 0

    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4o-mini"

    def embedding_cost(self) -> float:
        """Calculate embedding cost."""
        if self.embedding_model not in OPENAI_PRICING:
            return 0.0
        return self.embedding_tokens * OPENAI_PRICING[self.embedding_model]['input']

    def llm_cost(self) -> float:
        """Calculate LLM cost."""
        if self.llm_model not in OPENAI_PRICING:
            return 0.0
        pricing = OPENAI_PRICING[self.llm_model]
        input_cost = self.llm_input_tokens * pricing['input']
        output_cost = self.llm_output_tokens * pricing['output']
        return input_cost + output_cost

    def total_cost(self) -> float:
        """Total cost for this provider."""
        return self.embedding_cost() + self.llm_cost()


@dataclass
class EvaluationCost:
    """Cost breakdown for RAG evaluation (Ragas)."""
    num_samples: int = 0
    num_metrics: int = 0
    llm_input_tokens: int = 0
    llm_output_tokens: int = 0
    llm_model: str = "gpt-4o-mini"

    def cost(self) -> float:
        """Calculate evaluation cost."""
        if self.llm_model not in OPENAI_PRICING:
            return 0.0
        pricing = OPENAI_PRICING[self.llm_model]
        input_cost = self.llm_input_tokens * pricing['input']
        output_cost = self.llm_output_tokens * pricing['output']
        return input_cost + output_cost


@dataclass
class CostReport:
    """Comprehensive cost report for RAG evaluation."""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    providers: Dict[str, ProviderCost] = field(default_factory=dict)
    evaluation: Optional[EvaluationCost] = None

    def total_cost(self) -> float:
        """Total cost across all providers and evaluation."""
        provider_total = sum(p.total_cost() for p in self.providers.values())
        eval_cost = self.evaluation.cost() if self.evaluation else 0.0
        return provider_total + eval_cost

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON export."""
        return {
            'timestamp': self.timestamp,
            'total_cost': self.total_cost(),
            'providers': {
                name: {
                    'embedding_tokens': p.embedding_tokens,
                    'llm_input_tokens': p.llm_input_tokens,
                    'llm_output_tokens': p.llm_output_tokens,
                    'embedding_cost': p.embedding_cost(),
                    'llm_cost': p.llm_cost(),
                    'total_cost': p.total_cost(),
                    'num_queries': p.num_queries,
                    'num_documents': p.num_documents,
                }
                for name, p in self.providers.items()
            },
            'evaluation': {
                'num_samples': self.evaluation.num_samples,
                'num_metrics': self.evaluation.num_metrics,
                'llm_input_tokens': self.evaluation.llm_input_tokens,
                'llm_output_tokens': self.evaluation.llm_output_tokens,
                'cost': self.evaluation.cost(),
            } if self.evaluation else None,
        }

    def print_report(self) -> None:
        """Print human-readable cost report."""
        print("\n" + "=" * 80)
        print("💰 COST ANALYSIS REPORT")
        print("=" * 80)

        # Provider costs
        print("\n📊 Provider Costs:")
        for name, provider in self.providers.items():
            print(f"\n  {name}:")
            print(f"    Documents ingested: {provider.num_documents}")
            print(f"    Queries processed: {provider.num_queries}")
            print(f"    Embedding tokens: {provider.embedding_tokens:,}")
            print(f"    LLM input tokens: {provider.llm_input_tokens:,}")
            print(f"    LLM output tokens: {provider.llm_output_tokens:,}")
            print(f"    Embedding cost: ${provider.embedding_cost():.6f}")
            print(f"    LLM cost: ${provider.llm_cost():.6f}")
            print(f"    Total cost: ${provider.total_cost():.6f}")

        # Evaluation costs
        if self.evaluation:
            print(f"\n📊 Evaluation Costs (Ragas):")
            print(f"    Samples evaluated: {self.evaluation.num_samples}")
            print(f"    Metrics computed: {self.evaluation.num_metrics}")
            print(f"    LLM input tokens: {self.evaluation.llm_input_tokens:,}")
            print(f"    LLM output tokens: {self.evaluation.llm_output_tokens:,}")
            print(f"    Total cost: ${self.evaluation.cost():.6f}")

        # Total
        print(f"\n💵 TOTAL COST: ${self.total_cost():.6f}")
        print("=" * 80)


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.

    Uses rough approximation: 1 token ≈ 4 characters for English text.
    For more accurate counting, use tiktoken library.

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated token count
    """
    return len(text) // 4


def estimate_embedding_tokens(documents: List[str]) -> int:
    """
    Estimate embedding tokens for a list of documents.

    Args:
        documents: List of document texts

    Returns:
        Total estimated embedding tokens
    """
    return sum(estimate_tokens(doc) for doc in documents)
