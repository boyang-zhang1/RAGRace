"""Pydantic response models for the API."""

from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field


class RunSummary(BaseModel):
    """Summary information for a benchmark run (list view)."""

    run_id: str = Field(..., description="Unique run identifier")
    dataset: str = Field(..., description="Dataset name (e.g., 'qasper', 'policyqa')")
    split: str = Field(..., description="Dataset split (e.g., 'train', 'validation')")
    providers: List[str] = Field(..., description="List of provider names tested")
    status: str = Field(..., description="Run status (queued, running, completed, failed)")
    num_docs: int = Field(..., description="Number of documents processed")
    num_questions: int = Field(..., description="Total number of questions")
    started_at: datetime = Field(..., description="Run start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Run completion timestamp")
    duration_seconds: Optional[float] = Field(None, description="Total duration in seconds")

    class Config:
        from_attributes = True


class QuestionResult(BaseModel):
    """Result for a single question."""

    question_id: str
    question: str
    ground_truth: str
    response_answer: str
    response_context: List[str] = Field(default_factory=list, description="Retrieved chunks")
    response_latency_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    evaluation_scores: Dict[str, Any] = Field(default_factory=dict, description="Metric scores")

    class Config:
        from_attributes = True


class ProviderResult(BaseModel):
    """Provider results for a document."""

    provider: str
    status: str
    error: Optional[str] = None
    aggregated_scores: Dict[str, Any] = Field(default_factory=dict, description="Average scores by metric")
    duration_seconds: Optional[float] = None
    questions: List[QuestionResult] = Field(default_factory=list)

    class Config:
        from_attributes = True


class DocumentResult(BaseModel):
    """Document with results from all providers."""

    doc_id: str
    doc_title: str
    providers: Dict[str, ProviderResult] = Field(default_factory=dict, description="Results by provider name")

    class Config:
        from_attributes = True


class RunDetail(BaseModel):
    """Full details for a benchmark run including all results."""

    run_id: str
    dataset: str
    split: str
    providers: List[str]
    status: str
    num_docs: int
    num_questions: int
    config: Dict[str, Any] = Field(default_factory=dict, description="Full benchmark configuration")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    documents: List[DocumentResult] = Field(default_factory=list)

    class Config:
        from_attributes = True


class DatasetInfo(BaseModel):
    """Information about a dataset."""

    name: str = Field(..., description="Dataset identifier")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Dataset description")
    available_splits: List[str] = Field(..., description="Available data splits")
    num_documents: Optional[int] = Field(None, description="Total documents available")
    task_type: str = Field(..., description="Task type (e.g., 'question-answering')")

    class Config:
        from_attributes = True


class ResultsListResponse(BaseModel):
    """Response for list of runs."""

    runs: List[RunSummary]
    total: int = Field(..., description="Total number of runs matching filters")
    limit: int
    offset: int

    class Config:
        from_attributes = True


class ProviderPerformance(BaseModel):
    """Aggregated performance for a provider on a dataset."""

    provider: str
    num_documents: int = Field(..., description="Number of documents processed")
    num_runs: int = Field(..., description="Number of runs contributing to this aggregate")
    aggregated_scores: Dict[str, float] = Field(default_factory=dict, description="Average scores by metric")
    avg_duration_seconds: Optional[float] = Field(None, description="Average duration across documents")

    class Config:
        from_attributes = True


class DatasetPerformanceSummary(BaseModel):
    """Performance summary for all providers on a dataset."""

    dataset_name: str
    total_runs: int = Field(..., description="Total benchmark runs for this dataset")
    total_documents: int = Field(..., description="Unique documents tested")
    providers: List[ProviderPerformance] = Field(default_factory=list)
    last_run_date: Optional[datetime] = Field(None, description="Most recent run completion time")

    class Config:
        from_attributes = True


class ProviderDocumentDetail(BaseModel):
    """Document-level detail for a provider."""

    doc_id: str
    doc_title: str
    run_id: str
    run_date: datetime
    aggregated_scores: Dict[str, Any]
    duration_seconds: Optional[float]
    status: str

    class Config:
        from_attributes = True


class ProviderDetailResponse(BaseModel):
    """Detailed results for a specific provider on a dataset."""

    dataset_name: str
    provider: str
    total_documents: int
    total_runs: int
    overall_scores: Dict[str, float] = Field(default_factory=dict, description="Aggregated scores across all documents")
    documents: List[ProviderDocumentDetail] = Field(default_factory=list)

    class Config:
        from_attributes = True
