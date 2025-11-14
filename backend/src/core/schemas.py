"""
Data schemas for DocAgent-Arena benchmark.

All data structures are dataclasses for:
- Type safety
- Easy serialization (dataclasses.asdict)
- Clear API contracts
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from pathlib import Path


@dataclass
class DocumentData:
    """
    Represents a single document in the dataset.

    Supports both PDF-based (Qasper) and text-based (PolicyQA) datasets:
    - PDF-based: pdf_path is set, content in metadata is optional
    - Text-based: pdf_path is None, content stored in metadata['content']
    """
    doc_id: str
    doc_title: str
    pdf_path: Optional[Path]  # None for text-based datasets
    pdf_size_bytes: int  # File size for PDFs, text byte length for text-based
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dict for JSON serialization."""
        d = asdict(self)
        d['pdf_path'] = str(self.pdf_path) if self.pdf_path else None  # Path → str for JSON
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
    """Complete result for one provider on one document."""
    provider: str
    doc_id: str
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
            'doc_id': self.doc_id,
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
class DocumentResult:
    """Aggregated results for all providers on one document."""
    doc_id: str
    doc_title: str
    num_questions: int
    providers: Dict[str, ProviderResult] = field(default_factory=dict)
    winner: Dict[str, Any] = field(default_factory=dict)  # {metric: provider_name}
    timestamp: str = ""

    def to_dict(self) -> Dict:
        """Convert to dict for JSON serialization."""
        return {
            'doc_id': self.doc_id,
            'doc_title': self.doc_title,
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
    num_docs: int
    num_questions_total: int
    providers: List[str]
    results: List[DocumentResult] = field(default_factory=list)
    overall_winner: Dict[str, Any] = field(default_factory=dict)
    duration_seconds: float = 0.0
    timestamp_start: str = ""
    timestamp_end: str = ""

    def to_dict(self) -> Dict:
        """Convert to dict for JSON serialization."""
        return {
            'run_id': self.run_id,
            'config': self.config,
            'num_docs': self.num_docs,
            'num_questions_total': self.num_questions_total,
            'providers': self.providers,
            'results': [r.to_dict() for r in self.results],
            'overall_winner': self.overall_winner,
            'duration_seconds': self.duration_seconds,
            'timestamp_start': self.timestamp_start,
            'timestamp_end': self.timestamp_end
        }
