"""API endpoints for PDF parsing and comparison."""

import asyncio
import logging
import os
import random
import uuid
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from prisma import Prisma, Json
from pypdf import PdfReader, PdfWriter

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
    BattleFeedbackRequest,
    BattleFeedbackResponse,
    BattlePreference,
    BattleMetadata,
    BattleAssignment,
    BattleHistoryItem,
    BattleHistoryResponse,
    BattleProviderDetail,
    BattleDetailResponse,
    ProviderPricingInfo,
    PricingModelOption,
)
from api.db import get_db
from api.services.storage import SupabaseStorageService
from src.adapters.parsing.llamaindex_parser import LlamaIndexParser
from src.adapters.parsing.reducto_parser import ReductoParser
from src.adapters.parsing.landingai_parser import LandingAIParser
from src.adapters.parsing.base import ParseResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/parse", tags=["parsing"])

# Temporary storage directory for uploaded PDFs
TEMP_DIR = Path("data/temp")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_BATTLE_PROVIDERS = ["llamaindex", "reducto"]
DEFAULT_PROVIDER_CONFIGS: Dict[str, Dict[str, Any]] = {
    "llamaindex": {"mode": "agentic"},
    "reducto": {"mode": "standard"},
    "landingai": {"mode": "dpt-2"},
}
BATTLE_LABELS = ["A", "B", "C", "D"]
BATTLE_STORAGE_PREFIX = "user-upload"
PENDING_BATTLE_TASKS: Dict[str, asyncio.Task] = {}


def _extract_single_page(pdf_path: Path, page_number: int) -> Path:
    """Create a temporary PDF containing only the selected page."""
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    if page_number < 1 or page_number > total_pages:
        raise ValueError(f"Page {page_number} is out of range. PDF has {total_pages} pages.")

    writer = PdfWriter()
    writer.add_page(reader.pages[page_number - 1])

    output_path = TEMP_DIR / f"{pdf_path.stem}_page_{page_number}_{uuid.uuid4().hex}.pdf"
    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path


def _prepare_battle_assignments(providers: List[str]) -> (List[BattleAssignment], Dict[str, str]):
    """Shuffle providers and assign blind labels."""
    shuffled = providers[:]
    random.shuffle(shuffled)
    assignments: List[BattleAssignment] = []
    provider_to_label: Dict[str, str] = {}

    for idx, provider in enumerate(shuffled):
        if idx >= len(BATTLE_LABELS):
            break
        label = BATTLE_LABELS[idx]
        assignments.append(BattleAssignment(label=label, provider=provider))
        provider_to_label[provider] = label

    return assignments, provider_to_label


async def _persist_battle_run(
    prisma_client: Prisma,
    *,
    battle_id: str,
    upload_file_id: str,
    original_name: str,
    storage_input_path: Path,
    page_number: int,
    providers: List[str],
    provider_to_label: Dict[str, str],
    assignments: List[BattleAssignment],
    parse_results: List[ParseResult],
    configs: Dict[str, Dict[str, Any]],
):
    """Upload battle artifacts and persist run/results asynchronously."""

    client = prisma_client

    storage_url: Optional[str] = None
    # Construct Supabase storage path - this is our source of truth
    supabase_storage_path = f"{BATTLE_STORAGE_PREFIX}/{battle_id}.pdf"

    try:
        storage_service = SupabaseStorageService()
        storage_url = storage_service.upload(str(storage_input_path), supabase_storage_path)
        logger.info("Uploaded battle PDF to Supabase: %s (path: %s)", storage_url, supabase_storage_path)
    except Exception as exc:
        logger.error("Failed to upload battle PDF to Supabase: %s", exc)
        raise RuntimeError(f"Battle PDF upload to storage failed: {exc}")

    try:
        pricing_config = load_pricing_config()
    except Exception as exc:
        logger.debug("Pricing config unavailable for battle persistence: %s", exc)
        pricing_config = None

    provider_entries = []
    has_success = False

    for result in parse_results:
        usage = result.usage or {}
        cost_credits = None
        cost_usd = None

        if pricing_config:
            try:
                provider_cost = calculate_provider_cost(result.provider, usage, pricing_config)
                cost_credits = provider_cost.credits
                cost_usd = provider_cost.total_usd
            except Exception as exc:
                logger.debug("Cost calculation failed for %s: %s", result.provider, exc)

        pages_payload = [
            {
                "page_number": page.page_number,
                "markdown": page.markdown,
                "images": page.images,
                "metadata": _jsonify(page.metadata),
            }
            for page in result.pages
        ]
        if pages_payload:
            has_success = True

        # Get model config for this provider from configs dict
        # Note: We're not storing this in DB anymore, just in metadata

        provider_entries.append(
            {
                "provider": result.provider,
                "label": provider_to_label.get(result.provider, result.provider),
                "content": Json({"pages": pages_payload}),
                "totalPages": result.total_pages,
                "usage": Json(_jsonify(usage)),
                "costCredits": cost_credits,
                "costUsd": cost_usd,
                "processingTime": result.processing_time,
            }
        )

    status = "SUCCESS" if has_success else "ERROR"

    metadata = _jsonify({
        "configs": configs,
        "provider_labels": provider_to_label,
        "label_providers": {assignment.label: assignment.provider for assignment in assignments},
        "assignments": [assignment.model_dump() for assignment in assignments],
        "battle_mode": True,
    })

    try:
        await client.parsebattlerun.create(
            data={
                "id": battle_id,
                "uploadFileId": upload_file_id,
                "originalName": original_name,
                "storagePath": supabase_storage_path,
                "storageUrl": storage_url,
                "pageNumber": page_number,
                "providers": providers,
                "status": status,
                "metadata": Json(metadata),
                "providerResults": {"create": provider_entries},
            }
        )
    except Exception as exc:
        logger.error("Failed to persist battle run %s: %s", battle_id, exc)


def _normalize_preferred_labels(
    *,
    preference: Optional[BattlePreference],
    explicit_labels: Optional[List[str]],
    available_labels: List[str],
) -> List[str]:
    """Resolve preferred labels from either request payload or enum selection."""
    if explicit_labels is not None:
        normalized = []
        for label in explicit_labels:
            if label not in available_labels:
                raise HTTPException(status_code=400, detail=f"Invalid label '{label}' for this battle")
            if label not in normalized:
                normalized.append(label)
        return normalized

    if preference is None:
        raise HTTPException(status_code=400, detail="Provide either preferred_labels or preference")

    if preference == BattlePreference.A_BETTER:
        if not available_labels:
            raise HTTPException(status_code=400, detail="No providers available for battle")
        return [available_labels[0]]

    if preference == BattlePreference.B_BETTER:
        if len(available_labels) < 2:
            raise HTTPException(status_code=400, detail="Battle missing second provider")
        return [available_labels[1]]

    if preference == BattlePreference.BOTH_GOOD:
        return available_labels

    if preference == BattlePreference.BOTH_BAD:
        return []

    raise HTTPException(status_code=400, detail="Unsupported preference value")


@router.get("/available-providers")
async def get_available_providers():
    """
    Get list of available parsing providers.

    Returns:
        List of provider names that can be used for parsing
    """
    return ["llamaindex", "reducto", "landingai"]


@router.get("/pricing", response_model=List[ProviderPricingInfo])
async def get_provider_pricing():
    """Expose provider pricing metadata for frontend consumption."""
    try:
        pricing_config = load_pricing_config()
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return build_pricing_metadata(pricing_config)

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


def build_pricing_metadata(pricing_config: Dict[str, Any]) -> List[ProviderPricingInfo]:
    """Convert raw pricing config into API-friendly structures."""
    provider_infos: List[ProviderPricingInfo] = []

    for provider, provider_config in pricing_config.items():
        usd_per_credit = provider_config.get("usd_per_credit", 0.0)
        raw_models = provider_config.get("models") or []

        models: List[PricingModelOption] = []
        for entry in raw_models:
            credits_per_page = entry.get("credits_per_page")
            mode = entry.get("mode")
            if credits_per_page is None or not mode:
                continue

            api_params = entry.get("api") or {}
            option_config = {"mode": mode, **api_params}
            label = entry.get("label") or mode.replace("-", " ").title()
            description = entry.get("description")

            models.append(
                PricingModelOption(
                    label=label,
                    value=mode,
                    credits_per_page=credits_per_page,
                    usd_per_page=credits_per_page * usd_per_credit,
                    description=description,
                    config=option_config,
                )
            )

        provider_infos.append(
            ProviderPricingInfo(
                provider=provider,
                usd_per_credit=usd_per_credit,
                models=models,
            )
        )

    return provider_infos


def _get_source_value(source: Optional[Dict[str, Any]], key: str) -> Any:
    if not isinstance(source, dict):
        return None
    if key in source:
        return source[key]
    nested = source.get("config")
    if isinstance(nested, dict) and key in nested:
        return nested[key]
    return None


def _entry_matches(entry: Dict[str, Any], source: Optional[Dict[str, Any]]) -> bool:
    if not source:
        return False
    api_params = entry.get("api") or {}
    for key, value in api_params.items():
        if _get_source_value(source, key) != value:
            return False
    return True


def _select_pricing_entry(
    provider: str,
    provider_config: Dict[str, Any],
    *,
    mode: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    usage: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    models = provider_config.get("models") or []
    if not models:
        return None

    if mode:
        for entry in models:
            if entry.get("mode") == mode:
                return entry

    if config:
        for entry in models:
            if _entry_matches(entry, config):
                return entry

    if usage:
        for entry in models:
            if _entry_matches(entry, usage):
                return entry

    return models[0]


def _resolved_config_from_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    api_params = entry.get("api") or {}
    resolved = {"mode": entry.get("mode")}
    resolved.update(api_params)
    return resolved


def _resolve_provider_config(
    provider: str,
    user_config: Optional[Dict[str, Any]],
    pricing_config: Dict[str, Any]
) -> Dict[str, Any]:
    provider_pricing = pricing_config.get(provider)
    if not provider_pricing:
        raise ValueError(f"No pricing configuration defined for provider '{provider}'")

    mode = None
    if isinstance(user_config, dict):
        mode = user_config.get("mode")

    entry = _select_pricing_entry(provider, provider_pricing, mode=mode, config=user_config)
    if not entry:
        raise ValueError(f"No models configured for provider '{provider}'")

    return _resolved_config_from_entry(entry)


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

    entry = _select_pricing_entry(
        provider,
        provider_config,
        mode=_get_source_value(usage, "mode"),
        usage=usage,
    )
    if not entry:
        raise ValueError(f"Pricing configuration missing for provider '{provider}'")

    credits_per_page = entry.get("credits_per_page", 0)
    num_pages = usage.get("num_pages", 0)
    total_credits = credits_per_page * num_pages

    if total_credits == 0:
        total_credits = usage.get("credits", usage.get("total_credits", 0))
        if credits_per_page == 0 and num_pages:
            credits_per_page = total_credits / num_pages

    total_usd = total_credits * usd_per_credit

    details = {
        "mode": entry.get("mode"),
        "label": entry.get("label"),
        "num_pages": num_pages,
        "credits_per_page": credits_per_page,
    }
    api_params = entry.get("api") or {}
    if api_params:
        details.update(api_params)

    return ProviderCost(
        provider=provider,
        credits=total_credits,
        usd_per_credit=usd_per_credit,
        total_usd=total_usd,
        details=details,
    )


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
async def compare_parsers(request: ParseCompareRequest, db: Prisma = Depends(get_db)):
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

    # Determine providers
    requested_providers = request.providers or []
    battle_mode = len(requested_providers) == 0
    providers = requested_providers or DEFAULT_BATTLE_PROVIDERS.copy()
    providers = list(dict.fromkeys(providers))  # Deduplicate while preserving order

    if battle_mode and request.page_number is None:
        raise HTTPException(status_code=400, detail="Battle mode requires a specific page selection.")

    # Extract a single page if requested
    selected_pdf_path = pdf_path
    if request.page_number is not None:
        try:
            selected_pdf_path = _extract_single_page(pdf_path, request.page_number)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    try:
        pricing_config = load_pricing_config()
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    request_configs = request.configs or {}
    resolved_configs: Dict[str, Dict[str, Any]] = {}

    for provider in providers:
        user_config = request_configs.get(provider) or DEFAULT_PROVIDER_CONFIGS.get(provider) or {}
        try:
            resolved_config = _resolve_provider_config(provider, user_config, pricing_config)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        resolved_configs[provider] = resolved_config

    # Initialize parsers with backend environment API keys and configurations
    parsers: Dict[str, any] = {}

    try:
        if "llamaindex" in providers:
            config = resolved_configs.get("llamaindex")
            if not config:
                config = _resolve_provider_config("llamaindex", DEFAULT_PROVIDER_CONFIGS.get("llamaindex"), pricing_config)
            parse_mode = config.get("parse_mode", "parse_page_with_agent")
            model = config.get("model", "openai-gpt-4-1-mini")

            # Get API key from environment
            api_key = os.getenv("LLAMAINDEX_API_KEY")
            if not api_key:
                raise ValueError("LLAMAINDEX_API_KEY not configured in backend environment")

            parsers["llamaindex"] = LlamaIndexParser(
                api_key=api_key,
                parse_mode=parse_mode,
                model=model
            )

        if "reducto" in providers:
            config = resolved_configs.get("reducto")
            if not config:
                config = _resolve_provider_config("reducto", DEFAULT_PROVIDER_CONFIGS.get("reducto"), pricing_config)
            summarize_figures = config.get("summarize_figures", False)
            if "mode" in config:
                summarize_figures = config["mode"] == "complex"

            # Get API key from environment
            api_key = os.getenv("REDUCTO_API_KEY")
            if not api_key:
                raise ValueError("REDUCTO_API_KEY not configured in backend environment")

            parsers["reducto"] = ReductoParser(
                api_key=api_key,
                summarize_figures=summarize_figures
            )

        if "landingai" in providers:
            # Get API key from environment
            api_key = os.getenv("VISION_AGENT_API_KEY")
            if not api_key:
                raise ValueError("VISION_AGENT_API_KEY not configured in backend environment")

            # LandingAI has no configurable options yet
            parsers["landingai"] = LandingAIParser(api_key=api_key)

    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Configuration error: {str(e)}",
        )

    # Parse with all providers in parallel
    if not parsers:
        raise HTTPException(status_code=400, detail="No valid providers available for parsing.")

    parse_tasks = [parser.parse_pdf(selected_pdf_path) for parser in parsers.values()]

    try:
        parse_results = await asyncio.gather(*parse_tasks)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Parsing failed: {str(e)}"
        )

    # Format results
    results = {}
    for parse_result in parse_results:
        provider_config = resolved_configs.get(parse_result.provider, {})
        mode = provider_config.get("mode")
        if mode:
            usage_payload = parse_result.usage or {}
            if usage_payload.get("mode") != mode:
                usage_payload = {**usage_payload, "mode": mode}
            parse_result.usage = usage_payload

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

    battle_metadata: Optional[BattleMetadata] = None
    if battle_mode:
        battle_id = str(uuid.uuid4())
        assignments, provider_to_label = _prepare_battle_assignments(providers)
        battle_metadata = BattleMetadata(
            battle_id=battle_id,
            assignments=assignments,
        )

        # Fire-and-forget persistence so the response is not blocked
        task = asyncio.create_task(
            _persist_battle_run(
                prisma_client=db,
                battle_id=battle_id,
                upload_file_id=request.file_id,
                original_name=request.filename or f"{request.file_id}.pdf",
                storage_input_path=selected_pdf_path,
                page_number=request.page_number or 1,
                providers=providers,
                provider_to_label=provider_to_label,
                assignments=assignments,
                parse_results=parse_results,
                configs=resolved_configs,
            )
        )
        PENDING_BATTLE_TASKS[battle_id] = task
        task.add_done_callback(lambda _: PENDING_BATTLE_TASKS.pop(battle_id, None))

    return ParseCompareResponse(file_id=request.file_id, results=results, battle=battle_metadata)


@router.post("/battle-feedback", response_model=BattleFeedbackResponse)
async def submit_battle_feedback(request: BattleFeedbackRequest, db: Prisma = Depends(get_db)):
    """Persist user selection for a completed battle."""

    battle = await _ensure_battle_persisted(request.battle_id, db)

    if not battle:
        raise HTTPException(status_code=404, detail="Battle run not found")

    metadata = battle.metadata or {}
    assignments_raw = metadata.get("assignments") or []
    assignments: List[BattleAssignment] = []

    for entry in assignments_raw:
        try:
            assignments.append(BattleAssignment(**entry))
        except Exception:
            continue

    if not assignments:
        label_map = metadata.get("label_providers") or {}
        if isinstance(label_map, dict):
            for label, provider in label_map.items():
                assignments.append(BattleAssignment(label=label, provider=provider))

    if not assignments:
        provider_labels = metadata.get("provider_labels") or {}
        for provider, label in provider_labels.items():
            assignments.append(BattleAssignment(label=label, provider=provider))

    assignments.sort(key=lambda assignment: assignment.label)
    available_labels = [assignment.label for assignment in assignments]

    preferred_labels = _normalize_preferred_labels(
        preference=request.preference,
        explicit_labels=request.preferred_labels,
        available_labels=available_labels,
    )

    feedback_data = {
        "preferredLabels": preferred_labels,
        "comment": request.comment,
        "revealedAt": datetime.utcnow(),
    }

    existing = await db.battlefeedback.find_unique(where={"battleId": request.battle_id})

    if existing:
        record = await db.battlefeedback.update(
            where={"battleId": request.battle_id},
            data=feedback_data,
        )
    else:
        record = await db.battlefeedback.create(
            data={
                "battleId": request.battle_id,
                **feedback_data,
            }
        )

    return BattleFeedbackResponse(
        battle_id=request.battle_id,
        preferred_labels=record.preferredLabels,
        comment=record.comment,
        assignments=assignments,
    )


async def _ensure_battle_persisted(battle_id: str, prisma_client: Prisma, timeout: float = 5.0):
    """Wait for pending persistence task to finish before querying battle."""
    client = prisma_client

    battle = await client.parsebattlerun.find_unique(where={"id": battle_id})
    if battle:
        return battle

    pending_task = PENDING_BATTLE_TASKS.get(battle_id)
    if not pending_task:
        return None

    try:
        await asyncio.wait_for(asyncio.shield(pending_task), timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning("Timed out waiting for battle %s persistence", battle_id)
    except Exception as exc:
        logger.error("Battle persistence task for %s failed: %s", battle_id, exc)

    return await client.parsebattlerun.find_unique(where={"id": battle_id})


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


@router.get("/battle-pdf/{battle_id}")
async def get_battle_pdf(battle_id: str, db: Prisma = Depends(get_db)):
    """
    Get the single-page battle PDF file for viewing from Supabase storage.

    Downloads from Supabase Storage and returns the PDF.

    Args:
        battle_id: UUID of the battle

    Returns:
        FileResponse with single-page PDF content

    Raises:
        HTTPException: If battle or file not found
    """
    battle = await db.parsebattlerun.find_unique(where={"id": battle_id})

    if not battle:
        raise HTTPException(status_code=404, detail=f"Battle not found: {battle_id}")

    # Primary path: Download from Supabase Storage
    try:
        storage_service = SupabaseStorageService()
        logger.info(f"Downloading battle PDF from Supabase: {battle.storagePath}")
        temp_pdf_path = storage_service.download_to_temp(battle.storagePath)

        return FileResponse(
            temp_pdf_path,
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename=battle_{battle_id}_page_{battle.pageNumber}.pdf"},
        )
    except Exception as e:
        logger.error(f"Failed to download battle PDF from Supabase (path: {battle.storagePath}): {e}")

        # Fallback: Try to find local file for backwards compatibility with old records
        storage_path = Path(battle.storagePath)
        if storage_path.exists() and storage_path.is_file():
            logger.info(f"Found local battle PDF: {storage_path}")
            return FileResponse(
                storage_path,
                media_type="application/pdf",
                headers={"Content-Disposition": f"inline; filename=battle_{battle_id}_page_{battle.pageNumber}.pdf"},
            )

        # Last resort: Search for old battles using pattern {uploadFileId}_page_{pageNumber}_*.pdf
        pattern = f"{battle.uploadFileId}_page_{battle.pageNumber}_*.pdf"
        matching_files = list(TEMP_DIR.glob(pattern))

        if matching_files:
            pdf_path = matching_files[0]
            logger.info(f"Found battle PDF via pattern match: {pdf_path}")
            return FileResponse(
                pdf_path,
                media_type="application/pdf",
                headers={"Content-Disposition": f"inline; filename=battle_{battle_id}_page_{battle.pageNumber}.pdf"},
            )

        raise HTTPException(
            status_code=404,
            detail=f"Battle PDF not found. Storage path: {battle.storagePath}, Upload ID: {battle.uploadFileId}, Page: {battle.pageNumber}"
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
def _jsonify(value: Any) -> Any:
    """Convert arbitrary objects to JSON-serializable structures."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _jsonify(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonify(v) for v in value]
    return str(value)




@router.get("/battles", response_model=BattleHistoryResponse)
async def get_battle_history(
    page: int = 1,
    limit: int = 10,
    db: Prisma = Depends(get_db)
):
    """
    Get paginated list of battle history (only battles with feedback).

    Args:
        page: Page number (1-indexed)
        limit: Number of items per page

    Returns:
        BattleHistoryResponse with list of battles that have feedback
    """
    if page < 1:
        page = 1
    if limit < 1 or limit > 100:
        limit = 10

    skip = (page - 1) * limit

    try:
        pricing_config = load_pricing_config()
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    # Get total count of battles WITH feedback only
    total = await db.parsebattlerun.count(
        where={
            "feedback": {
                "is": {}
            }
        }
    )

    # Get battles with feedback only
    battles = await db.parsebattlerun.find_many(
        where={
            "feedback": {
                "is": {}
            }
        },
        skip=skip,
        take=limit,
        order={"createdAt": "desc"},
        include={
            "feedback": True,
            "providerResults": True,
        }
    )

    items = []
    for battle in battles:
        # Determine winner from feedback
        winner = None
        preferred_labels = None
        if battle.feedback:
            preferred_labels = battle.feedback.preferredLabels
            metadata = battle.metadata or {}
            label_to_provider = metadata.get("label_providers") or {}

            if len(preferred_labels) == 1:
                # One winner
                winner_label = preferred_labels[0]
                winner = label_to_provider.get(winner_label, winner_label)
            elif len(preferred_labels) > 1:
                winner = "tie"
            elif len(preferred_labels) == 0:
                winner = "none"

        metadata = battle.metadata or {}
        configs = metadata.get("configs") or {}
        if not isinstance(configs, dict):
            configs = {}
        configs = {key: (value or {}) for key, value in configs.items()}

        model_display_names: Dict[str, str] = {}
        provider_results = {result.provider: result for result in (battle.providerResults or [])}
        metadata_updated = False

        providers = battle.providers or []
        provider_keys = set(providers)
        provider_keys.update(configs.keys())

        if not provider_keys:
            provider_keys.update(DEFAULT_BATTLE_PROVIDERS)

        for provider in provider_keys:
            provider_pricing = pricing_config.get(provider, {})
            config_entry = configs.get(provider) or {}
            usage = None
            provider_result = provider_results.get(provider)
            if provider_result and provider_result.usage:
                usage = provider_result.usage

            entry = _select_pricing_entry(
                provider,
                provider_pricing,
                mode=_get_source_value(config_entry, "mode"),
                config=config_entry,
                usage=usage,
            )

            if entry:
                model_display_names[provider] = entry.get("label") or entry.get("mode") or provider
                resolved_config = _resolved_config_from_entry(entry)
                if configs.get(provider) != resolved_config:
                    configs[provider] = resolved_config
                    metadata_updated = True
            else:
                model_display_names[provider] = provider

        if metadata_updated:
            try:
                metadata = {**metadata, "configs": configs}
                await db.parsebattlerun.update(
                    where={"id": battle.id},
                    data={"metadata": Json(_jsonify(metadata))},
                )
            except Exception as exc:
                logger.debug("Failed to backfill battle configs for %s: %s", battle.id, exc)

        items.append(BattleHistoryItem(
            battle_id=battle.id,
            original_name=battle.originalName,
            page_number=battle.pageNumber,
            created_at=battle.createdAt.isoformat(),
            winner=winner,
            preferred_labels=preferred_labels,
            model_display_names=model_display_names if model_display_names else None
        ))

    return BattleHistoryResponse(
        battles=items,
        total=total,
        page=page,
        limit=limit
    )


@router.get("/battles/{battle_id}", response_model=BattleDetailResponse)
async def get_battle_detail(
    battle_id: str,
    db: Prisma = Depends(get_db)
):
    """
    Get complete battle details.

    Args:
        battle_id: UUID of the battle

    Returns:
        BattleDetailResponse with full battle details

    Raises:
        HTTPException: If battle not found
    """
    battle = await db.parsebattlerun.find_unique(
        where={"id": battle_id},
        include={
            "providerResults": True,
            "feedback": True
        }
    )

    if not battle:
        raise HTTPException(status_code=404, detail=f"Battle not found: {battle_id}")

    # Extract assignments from metadata
    metadata = battle.metadata or {}
    assignments_raw = metadata.get("assignments") or []
    assignments: List[BattleAssignment] = []

    for entry in assignments_raw:
        try:
            assignments.append(BattleAssignment(**entry))
        except Exception:
            continue

    if not assignments:
        label_map = metadata.get("label_providers") or {}
        for label, provider in label_map.items():
            assignments.append(BattleAssignment(label=label, provider=provider))

    # Build provider details
    provider_details = []
    for result in battle.providerResults:
        content_data = result.content or {}
        pages_data = content_data.get("pages", [])

        pages = [
            PageData(
                page_number=page["page_number"],
                markdown=page["markdown"],
                images=page.get("images", []),
                metadata=page.get("metadata", {})
            )
            for page in pages_data
        ]

        provider_result = ProviderParseResult(
            total_pages=result.totalPages,
            pages=pages,
            processing_time=result.processingTime,
            usage=result.usage or {}
        )

        provider_details.append(BattleProviderDetail(
            provider=result.provider,
            label=result.label,
            content=provider_result,
            cost_usd=result.costUsd,
            cost_credits=result.costCredits
        ))

    # Extract provider configs from metadata
    metadata = battle.metadata or {}
    provider_configs = metadata.get("configs") or None

    # Build feedback data
    feedback_data = None
    if battle.feedback:
        feedback_data = {
            "preferred_labels": battle.feedback.preferredLabels,
            "comment": battle.feedback.comment,
            "revealed_at": battle.feedback.revealedAt.isoformat() if battle.feedback.revealedAt else None
        }

    return BattleDetailResponse(
        battle_id=battle.id,
        original_name=battle.originalName,
        page_number=battle.pageNumber,
        upload_file_id=battle.uploadFileId,
        storage_url=battle.storageUrl,
        storage_path=battle.storagePath,
        created_at=battle.createdAt.isoformat(),
        providers=provider_details,
        feedback=feedback_data,
        assignments=assignments,
        provider_configs=provider_configs
    )
