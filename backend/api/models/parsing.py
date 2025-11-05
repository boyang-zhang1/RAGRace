"""
Request and response models for parsing API endpoints.
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field


class ProviderCost(BaseModel):
    """Cost breakdown for a single provider."""

    provider: str
    credits: float
    usd_per_credit: float
    total_usd: float
    details: Dict[str, Any] = {}


class CostComparisonResponse(BaseModel):
    """Response with cost breakdown for all providers."""

    file_id: str
    costs: Dict[str, ProviderCost]
    total_usd: float


class LlamaIndexConfig(BaseModel):
    """Configuration for LlamaIndex parsing."""

    parse_mode: str = Field(
        default="parse_page_with_agent",
        description="Parse mode: parse_page_with_agent or parse_page_with_llm"
    )
    model: str = Field(
        default="openai-gpt-4-1-mini",
        description="Model to use for parsing"
    )


class ReductoConfig(BaseModel):
    """Configuration for Reducto parsing."""

    mode: str = Field(
        default="standard",
        description="Mode: standard (1 credit/page) or complex (2 credits/page)"
    )
    summarize_figures: bool = Field(
        default=False,
        description="Enable VLM enhancement for complex pages"
    )


class LandingAIConfig(BaseModel):
    """Configuration for LandingAI parsing."""

    model: str = Field(
        default="dpt-2",
        description="Model to use (currently only dpt-2 is available)"
    )


class ParseCompareRequest(BaseModel):
    """
    Request model for comparing PDF parsing across providers.

    Example:
        {
            "file_id": "550e8400-e29b-41d4-a716-446655440000",
            "providers": ["llamaindex", "reducto"],
            "api_keys": {
                "llamaindex": "llx_...",
                "reducto": "sk_..."
            },
            "configs": {
                "llamaindex": {"parse_mode": "parse_page_with_agent", "model": "openai-gpt-4-1-mini"},
                "reducto": {"mode": "standard", "summarize_figures": false}
            }
        }
    """

    file_id: str = Field(..., description="UUID of uploaded file")
    providers: List[str] = Field(
        default=["llamaindex", "reducto"],
        description="List of parser providers to compare",
    )
    api_keys: Dict[str, str] = Field(
        ..., description="API keys for each provider"
    )
    configs: Dict[str, Dict[str, Any]] = Field(
        default={},
        description="Optional configurations for each provider"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "550e8400-e29b-41d4-a716-446655440000",
                "providers": ["llamaindex", "reducto"],
                "api_keys": {
                    "llamaindex": "llx_...",
                    "reducto": "sk_..."
                },
                "configs": {
                    "llamaindex": {"parse_mode": "parse_page_with_agent", "model": "openai-gpt-4-1-mini"},
                    "reducto": {"mode": "standard", "summarize_figures": False}
                }
            }
        }


class PageCountRequest(BaseModel):
    """Request model for getting page count of an uploaded PDF."""

    file_id: str = Field(..., description="UUID of uploaded file")


class PageCountResponse(BaseModel):
    """Response model for page count."""

    file_id: str = Field(..., description="UUID of the file")
    page_count: int = Field(..., description="Number of pages in the PDF")
    filename: str = Field(..., description="Original filename")


class UploadResponse(BaseModel):
    """
    Response model for file upload.

    Example:
        {
            "file_id": "550e8400-e29b-41d4-a716-446655440000",
            "filename": "document.pdf"
        }
    """

    file_id: str = Field(..., description="UUID for uploaded file")
    filename: str = Field(..., description="Original filename")

    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "document.pdf",
            }
        }


class PageData(BaseModel):
    """Data for a single parsed page."""

    page_number: int
    markdown: str
    images: List[str] = []
    metadata: Dict[str, Any] = {}


class ProviderParseResult(BaseModel):
    """Parsing result from a single provider."""

    total_pages: int
    pages: List[PageData]
    processing_time: float
    usage: Dict[str, Any] = {}


class ParseCompareResponse(BaseModel):
    """
    Response model for parse comparison.

    Example:
        {
            "file_id": "550e8400-e29b-41d4-a716-446655440000",
            "results": {
                "llamaindex": {
                    "total_pages": 5,
                    "pages": [...],
                    "processing_time": 12.5
                },
                "reducto": {
                    "total_pages": 5,
                    "pages": [...],
                    "processing_time": 8.3
                }
            }
        }
    """

    file_id: str = Field(..., description="UUID of the parsed file")
    results: Dict[str, ProviderParseResult] = Field(
        ..., description="Parsing results keyed by provider name"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "550e8400-e29b-41d4-a716-446655440000",
                "results": {
                    "llamaindex": {
                        "total_pages": 5,
                        "pages": [
                            {
                                "page_number": 1,
                                "markdown": "# Introduction\n\nThis is page 1...",
                                "images": [],
                                "metadata": {},
                            }
                        ],
                        "processing_time": 12.5,
                    }
                },
            }
        }
