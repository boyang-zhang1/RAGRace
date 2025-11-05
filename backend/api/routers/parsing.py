"""
API endpoints for PDF parsing and comparison.
"""

import asyncio
import os
import uuid
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from api.models.parsing import (
    ParseCompareRequest,
    ParseCompareResponse,
    UploadResponse,
    ProviderParseResult,
    PageData,
)
from src.adapters.parsing.llamaindex_parser import LlamaIndexParser
from src.adapters.parsing.reducto_parser import ReductoParser
from src.adapters.parsing.landingai_parser import LandingAIParser

router = APIRouter(prefix="/parse", tags=["parsing"])

# Temporary storage directory for uploaded PDFs
TEMP_DIR = Path("data/temp")
TEMP_DIR.mkdir(parents=True, exist_ok=True)


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


@router.post("/compare", response_model=ParseCompareResponse)
async def compare_parsers(request: ParseCompareRequest):
    """
    Compare PDF parsing across multiple providers.

    Args:
        request: ParseCompareRequest with file_id and provider list

    Returns:
        ParseCompareResponse with parsing results from each provider

    Raises:
        HTTPException: If file not found or parsing fails
    """
    # Validate file exists
    pdf_path = TEMP_DIR / f"{request.file_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {request.file_id}. Please upload the file first.",
        )

    # Initialize parsers
    parsers: Dict[str, any] = {}

    try:
        if "llamaindex" in request.providers:
            parsers["llamaindex"] = LlamaIndexParser()

        if "reducto" in request.providers:
            parsers["reducto"] = ReductoParser()

        if "landingai" in request.providers:
            parsers["landingai"] = LandingAIParser()

    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize parsers: {str(e)}. Check API keys in .env file.",
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
