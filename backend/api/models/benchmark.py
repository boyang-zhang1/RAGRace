"""
Request and response models for benchmark API endpoints.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class BenchmarkRequest(BaseModel):
    """
    Request model for creating a new benchmark run.

    Example:
        {
            "dataset": "qasper",
            "split": "train",
            "providers": ["llamaindex"],
            "max_docs": 2,
            "max_questions_per_doc": 3,
            "filter_unanswerable": true,
            "api_keys": {
                "openai": "sk-...",
                "llamaindex": "llx-..."
            }
        }
    """
    dataset: str = Field(..., description="Dataset name (qasper, policyqa, squad2)")
    split: str = Field(default="train", description="Dataset split (train, validation, test)")
    providers: List[str] = Field(..., description="List of provider names to benchmark")
    max_docs: Optional[int] = Field(default=None, description="Maximum number of documents (null = all)")
    max_questions_per_doc: Optional[int] = Field(default=None, description="Maximum questions per document (null = all)")
    filter_unanswerable: bool = Field(default=True, description="Filter out unanswerable questions")
    api_keys: Optional[Dict[str, str]] = Field(
        default=None,
        description="API keys for providers. Keys: 'openai', 'llamaindex', 'vision_agent', 'reducto'. If not provided, falls back to environment variables."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "dataset": "qasper",
                "split": "train",
                "providers": ["llamaindex"],
                "max_docs": 2,
                "max_questions_per_doc": 3,
                "filter_unanswerable": True,
                "api_keys": {
                    "openai": "sk-...",
                    "llamaindex": "llx-..."
                }
            }
        }


class BenchmarkResponse(BaseModel):
    """
    Response model for benchmark creation.

    Example:
        {
            "run_id": "run_20251101_143000",
            "status": "completed",
            "message": "Benchmark completed successfully",
            "duration_seconds": 145.3
        }
    """
    run_id: str = Field(..., description="Unique run identifier")
    status: str = Field(..., description="Run status (running, completed, failed)")
    message: str = Field(..., description="Status message or error details")
    duration_seconds: Optional[float] = Field(default=None, description="Execution time in seconds (if completed)")

    class Config:
        json_schema_extra = {
            "example": {
                "run_id": "run_20251101_143000",
                "status": "completed",
                "message": "Benchmark completed successfully",
                "duration_seconds": 145.3
            }
        }
