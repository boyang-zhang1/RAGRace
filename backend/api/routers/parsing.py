"""
API endpoints for PDF parsing and comparison.
"""

import asyncio
import os
import uuid
import yaml
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pypdf import PdfReader

from api.models.parsing import (
    ParseCompareRequest,
    ParseCompareResponse,
    UploadResponse,
    ProviderParseResult,
    PageData,
    ProviderCost,
    CostComparisonResponse,
    PageCountRequest,
    PageCountResponse,
)
from src.adapters.parsing.llamaindex_parser import LlamaIndexParser
from src.adapters.parsing.reducto_parser import ReductoParser
from src.adapters.parsing.landingai_parser import LandingAIParser

router = APIRouter(prefix="/parse", tags=["parsing"])

# Temporary storage directory for uploaded PDFs
TEMP_DIR = Path("data/temp")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Pricing configuration path
# Try multiple possible locations
def get_pricing_config_path() -> Path:
    """Find pricing config file in various possible locations."""
    possible_paths = [
        Path(__file__).parent.parent.parent / "config" / "parsing_pricing.yaml",  # /app/backend/config/
        Path("config/parsing_pricing.yaml"),  # If running from backend dir
        Path("backend/config/parsing_pricing.yaml"),  # If running from project root
    ]

    for path in possible_paths:
        if path.exists():
            return path

    # If none found, return the first one (will error with clear path)
    return possible_paths[0]

PRICING_CONFIG_PATH = get_pricing_config_path()


def load_pricing_config() -> Dict:
    """Load pricing configuration from YAML file."""
    try:
        if not PRICING_CONFIG_PATH.exists():
            raise FileNotFoundError(f"Pricing config not found at: {PRICING_CONFIG_PATH.absolute()}")
        with open(PRICING_CONFIG_PATH, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise ValueError(f"Failed to load pricing config from {PRICING_CONFIG_PATH.absolute()}: {str(e)}")


def calculate_provider_cost(provider: str, usage: Dict, pricing_config: Dict) -> ProviderCost:
    """
    Calculate cost for a provider based on usage information.

    Args:
        provider: Provider name (llamaindex, reducto, landingai)
        usage: Usage information from parse result
        pricing_config: Loaded pricing configuration

    Returns:
        ProviderCost with cost breakdown
    """
    provider_config = pricing_config.get(provider, {})
    usd_per_credit = provider_config.get("usd_per_credit", 0)

    if provider == "llamaindex":
        # Calculate based on parse_mode + model configuration
        parse_mode = usage.get("parse_mode", "")
        model = usage.get("model", "")
        num_pages = usage.get("num_pages", 0)

        # Find matching model config
        models = provider_config.get("models", [])
        credits_per_page = None
        for model_config in models:
            if model_config.get("parse_mode") == parse_mode and model_config.get("model") == model:
                credits_per_page = model_config.get("credits_per_page")
                break

        if credits_per_page is None:
            # Default if not found
            credits_per_page = 10

        total_credits = num_pages * credits_per_page
        total_usd = total_credits * usd_per_credit

        return ProviderCost(
            provider=provider,
            credits=total_credits,
            usd_per_credit=usd_per_credit,
            total_usd=total_usd,
            details={
                "parse_mode": parse_mode,
                "model": model,
                "num_pages": num_pages,
                "credits_per_page": credits_per_page,
            }
        )

    elif provider == "reducto":
        # Get mode from usage to determine credits per page
        mode = usage.get("mode", "standard")
        num_pages = usage.get("num_pages", 0)

        # Look up credits_per_page from pricing config based on mode
        models = provider_config.get("models", [])
        credits_per_page = None
        for model_config in models:
            if model_config.get("mode") == mode:
                credits_per_page = model_config.get("credits_per_page")
                break

        # Fall back to API response credits if config lookup fails
        if credits_per_page is None:
            credits = usage.get("credits", 0)
            credits_per_page = (credits / num_pages) if num_pages > 0 else 1
            total_credits = credits
        else:
            total_credits = num_pages * credits_per_page

        total_usd = total_credits * usd_per_credit

        return ProviderCost(
            provider=provider,
            credits=total_credits,
            usd_per_credit=usd_per_credit,
            total_usd=total_usd,
            details={
                "mode": mode,
                "num_pages": num_pages,
                "credits_per_page": credits_per_page,
                "summarize_figures": usage.get("summarize_figures", False),
            }
        )

    elif provider == "landingai":
        # Fixed rate: 3 credits per page
        total_credits = usage.get("total_credits", 0)
        num_pages = usage.get("num_pages", 0)
        credits_per_page = usage.get("credits_per_page", 3)
        total_usd = total_credits * usd_per_credit

        return ProviderCost(
            provider=provider,
            credits=total_credits,
            usd_per_credit=usd_per_credit,
            total_usd=total_usd,
            details={
                "num_pages": num_pages,
                "credits_per_page": credits_per_page,
            }
        )

    else:
        raise ValueError(f"Unknown provider: {provider}")


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file for parsing.

    Args:
        file: PDF file uploaded by user

    Returns:
        UploadResponse with file_id and filename

    Raises:
        HTTPException: If file is not a PDF
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Generate unique file ID
    file_id = str(uuid.uuid4())

    # Save to temporary storage
    temp_path = TEMP_DIR / f"{file_id}.pdf"

    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to save uploaded file: {str(e)}"
        )

    return UploadResponse(file_id=file_id, filename=file.filename)


@router.post("/page-count", response_model=PageCountResponse)
async def get_page_count(request: PageCountRequest):
    """
    Get the page count of an uploaded PDF file.

    Args:
        request: PageCountRequest with file_id

    Returns:
        PageCountResponse with page count and filename

    Raises:
        HTTPException: If file not found or invalid PDF
    """
    # Validate file exists
    pdf_path = TEMP_DIR / f"{request.file_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {request.file_id}. Please upload the file first.",
        )

    try:
        # Read PDF and get page count
        reader = PdfReader(pdf_path)
        page_count = len(reader.pages)

        # Extract original filename from metadata if available
        # For now, we'll use the file_id as filename
        filename = f"{request.file_id}.pdf"

        return PageCountResponse(
            file_id=request.file_id,
            page_count=page_count,
            filename=filename
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read PDF: {str(e)}"
        )


@router.post("/compare", response_model=ParseCompareResponse)
async def compare_parsers(request: ParseCompareRequest):
    """
    Compare PDF parsing across multiple providers.

    Args:
        request: ParseCompareRequest with file_id, provider list, and API keys

    Returns:
        ParseCompareResponse with parsing results from each provider

    Raises:
        HTTPException: If file not found, missing API keys, or parsing fails
    """
    # Validate file exists
    pdf_path = TEMP_DIR / f"{request.file_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {request.file_id}. Please upload the file first.",
        )

    # Validate that each provider has a corresponding API key
    missing_keys = [p for p in request.providers if p not in request.api_keys]
    if missing_keys:
        raise HTTPException(
            status_code=400,
            detail=f"Missing API keys for providers: {', '.join(missing_keys)}",
        )

    # Initialize parsers with user-provided API keys and configurations
    parsers: Dict[str, any] = {}

    try:
        if "llamaindex" in request.providers:
            # Get LlamaIndex config or use defaults
            config = request.configs.get("llamaindex", {})
            parse_mode = config.get("parse_mode", "parse_page_with_agent")
            model = config.get("model", "openai-gpt-4-1-mini")
            parsers["llamaindex"] = LlamaIndexParser(
                api_key=request.api_keys["llamaindex"],
                parse_mode=parse_mode,
                model=model
            )

        if "reducto" in request.providers:
            # Get Reducto config or use defaults
            config = request.configs.get("reducto", {})
            summarize_figures = config.get("summarize_figures", False)
            # Handle mode field (standard/complex) as well
            if "mode" in config:
                summarize_figures = config["mode"] == "complex"
            parsers["reducto"] = ReductoParser(
                api_key=request.api_keys["reducto"],
                summarize_figures=summarize_figures
            )

        if "landingai" in request.providers:
            # LandingAI has no configurable options yet
            parsers["landingai"] = LandingAIParser(api_key=request.api_keys["landingai"])

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid API key: {str(e)}",
        )

    # Parse with all providers in parallel
    parse_tasks = [parser.parse_pdf(pdf_path) for parser in parsers.values()]

    try:
        parse_results = await asyncio.gather(*parse_tasks)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Parsing failed: {str(e)}"
        )

    # Format results
    results = {}
    for parse_result in parse_results:
        provider_result = ProviderParseResult(
            total_pages=parse_result.total_pages,
            pages=[
                PageData(
                    page_number=page.page_number,
                    markdown=page.markdown,
                    images=page.images,
                    metadata=page.metadata,
                )
                for page in parse_result.pages
            ],
            processing_time=parse_result.processing_time,
            usage=parse_result.usage,
        )
        results[parse_result.provider] = provider_result

    return ParseCompareResponse(file_id=request.file_id, results=results)


@router.get("/file/{file_id}")
async def get_pdf(file_id: str):
    """
    Get the original PDF file for viewing.

    Args:
        file_id: UUID of the uploaded file

    Returns:
        FileResponse with PDF content

    Raises:
        HTTPException: If file not found
    """
    pdf_path = TEMP_DIR / f"{file_id}.pdf"

    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_id}")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={file_id}.pdf"},
    )


@router.post("/calculate-cost", response_model=CostComparisonResponse)
async def calculate_cost(request: ParseCompareResponse):
    """
    Calculate costs for all providers in a parse result.

    Args:
        request: ParseCompareResponse with usage information

    Returns:
        CostComparisonResponse with cost breakdown

    Raises:
        HTTPException: If cost calculation fails
    """
    try:
        pricing_config = load_pricing_config()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    costs = {}
    total_usd = 0.0

    for provider, result in request.results.items():
        try:
            cost = calculate_provider_cost(provider, result.usage, pricing_config)
            costs[provider] = cost
            total_usd += cost.total_usd
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to calculate cost for {provider}: {str(e)}"
            )

    return CostComparisonResponse(
        file_id=request.file_id,
        costs=costs,
        total_usd=total_usd,
    )
