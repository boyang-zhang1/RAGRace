"""
Data schemas for RAGRace benchmark.

All data structures are dataclasses for:
- Type safety
- Easy serialization (dataclasses.asdict)
- Clear API contracts
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from pathlib import Path


@dataclass
class PaperData:
    """Represents a single paper in the dataset."""
    paper_id: str
    paper_title: str
    pdf_path: Path
    pdf_size_bytes: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dict for JSON serialization."""
        d = asdict(self)
        d['pdf_path'] = str(self.pdf_path)  # Path → str for JSON
        return d


@dataclass
class QuestionData:
    """Represents a single question."""
    question_id: str
    question: str
    ground_truth: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dict for JSON serialization."""
        return asdict(self)


@dataclass
class QuestionResult:
    """Result for a single question from a provider."""
    question_id: str
    question: str
    ground_truth: str
    response_answer: str
    response_context: List[str]
    response_latency_ms: float
    response_metadata: Dict[str, Any]
    evaluation_scores: Dict[str, float]  # {metric_name: score}

    def to_dict(self) -> Dict:
        """Convert to dict for JSON serialization."""
        return asdict(self)


@dataclass
class ProviderResult:
    """Complete result for one provider on one paper."""
    provider: str
    paper_id: str
    status: str  # "success" | "error"
    error: Optional[str] = None
    index_id: Optional[str] = None
    questions: List[QuestionResult] = field(default_factory=list)
    aggregated_scores: Dict[str, float] = field(default_factory=dict)
    duration_seconds: float = 0.0
    timestamp_start: str = ""
    timestamp_end: str = ""

    def to_dict(self) -> Dict:
        """Convert to dict for JSON serialization."""
        return {
            'provider': self.provider,
            'paper_id': self.paper_id,
            'status': self.status,
            'error': self.error,
            'index_id': self.index_id,
            'questions': [q.to_dict() for q in self.questions],
            'aggregated_scores': self.aggregated_scores,
            'duration_seconds': self.duration_seconds,
            'timestamp_start': self.timestamp_start,
            'timestamp_end': self.timestamp_end
        }


@dataclass
class PaperResult:
    """Aggregated results for all providers on one paper."""
    paper_id: str
    paper_title: str
    num_questions: int
    providers: Dict[str, ProviderResult] = field(default_factory=dict)
    winner: Dict[str, Any] = field(default_factory=dict)  # {metric: provider_name}
    timestamp: str = ""

    def to_dict(self) -> Dict:
        """Convert to dict for JSON serialization."""
        return {
            'paper_id': self.paper_id,
            'paper_title': self.paper_title,
            'num_questions': self.num_questions,
            'providers': {name: result.to_dict() for name, result in self.providers.items()},
            'winner': self.winner,
            'timestamp': self.timestamp
        }


@dataclass
class RunSummary:
    """Overall benchmark run summary."""
    run_id: str
    config: Dict[str, Any]
    num_papers: int
    num_questions_total: int
    providers: List[str]
    results: List[PaperResult] = field(default_factory=list)
    overall_winner: Dict[str, Any] = field(default_factory=dict)
    duration_seconds: float = 0.0
    timestamp_start: str = ""
    timestamp_end: str = ""

    def to_dict(self) -> Dict:
        """Convert to dict for JSON serialization."""
        return {
            'run_id': self.run_id,
            'config': self.config,
            'num_papers': self.num_papers,
            'num_questions_total': self.num_questions_total,
            'providers': self.providers,
            'results': [r.to_dict() for r in self.results],
            'overall_winner': self.overall_winner,
            'duration_seconds': self.duration_seconds,
            'timestamp_start': self.timestamp_start,
            'timestamp_end': self.timestamp_end
        }
