"""LlamaIndex (LlamaParse) parsing adapter."""

import os
import time
from pathlib import Path
from typing import Dict, Any

from llama_parse import LlamaParse

from .base import BaseParseAdapter, PageResult, ParseResult


class LlamaIndexParser(BaseParseAdapter):
    """Parser using LlamaIndex's LlamaParse API."""

    def __init__(self, api_key: str, parse_mode: str = "parse_page_with_agent", model: str = "openai-gpt-4-1-mini"):
        """
        Initialize LlamaIndex parser.

        Args:
            api_key: API key for LlamaParse (required).
            parse_mode: Parsing mode (default: "parse_page_with_agent")
            model: Model to use (default: "openai-gpt-4-1-mini")

        Raises:
            ValueError: If api_key is empty or None.
        """
        if not api_key:
            raise ValueError("LlamaIndex API key is required")
        self.api_key = api_key
        self.parse_mode = parse_mode
        self.model = model

    async def parse_pdf(self, pdf_path: Path) -> ParseResult:
        """
        Parse PDF using LlamaParse with page-by-page splitting.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            ParseResult with markdown content per page
        """
        start_time = time.time()

        # Initialize parser with optimal settings for markdown output
        # For parse_page_with_llm mode, model parameter may not be needed
        parser_kwargs = {
            "api_key": self.api_key,
            "parse_mode": self.parse_mode,
            "high_res_ocr": True,  # Better quality for tables/figures
            "adaptive_long_table": True,  # Handle long tables spanning pages
            "outlined_table_extraction": True,  # Preserve table structure
            "output_tables_as_HTML": True,  # Better table rendering in markdown
            "page_separator": "\n\n---\n\n",  # Clear page breaks
        }

        # Only add model parameter for agent-based parsing modes
        if self.parse_mode == "parse_page_with_agent":
            parser_kwargs["model"] = self.model

        parser = LlamaParse(**parser_kwargs)

        # Parse the PDF (async)
        result = await parser.aparse(str(pdf_path))

        # Debug: Save the raw result to see its structure (optional, only if temp dir exists)
        import json
        try:
            temp_dir = Path("data/temp")
            if temp_dir.exists():
                debug_file = temp_dir / "llamaparse_debug.json"
                # Try to serialize result for inspection
                debug_data = {
                    "type": str(type(result)),
                    "dir": [x for x in dir(result) if not x.startswith('_')],
                    "pages_type": str(type(result.pages)) if hasattr(result, 'pages') else None,
                    "pages_length": len(result.pages) if hasattr(result, 'pages') else None,
                }
                if hasattr(result, 'pages') and len(result.pages) > 0:
                    first_page = result.pages[0]
                    debug_data["first_page_type"] = str(type(first_page))
                    debug_data["first_page_dir"] = [x for x in dir(first_page) if not x.startswith('_')]
                    debug_data["first_page_md"] = str(first_page.md) if hasattr(first_page, 'md') else None
                    debug_data["first_page_images_type"] = str(type(first_page.images)) if hasattr(first_page, 'images') else None
                    if hasattr(first_page, 'images') and first_page.images:
                        debug_data["first_image_type"] = str(type(first_page.images[0]))
                        debug_data["first_image_dir"] = [x for x in dir(first_page.images[0]) if not x.startswith('_')]

                with open(debug_file, 'w') as f:
                    json.dump(debug_data, f, indent=2)
        except Exception as e:
            # Silently ignore debug file errors
            pass

        # Extract page-by-page markdown
        pages = []
        for i, page in enumerate(result.pages, 1):
            # Convert ImageItem objects to strings (image names or URLs)
            image_refs = []
            if page.images:
                for img in page.images:
                    if hasattr(img, 'name'):
                        image_refs.append(img.name)
                    elif hasattr(img, 'url'):
                        image_refs.append(img.url)
                    elif isinstance(img, str):
                        image_refs.append(img)
                    else:
                        image_refs.append(str(img))

            pages.append(
                PageResult(
                    page_number=i,
                    markdown=page.md or "",  # Markdown content
                    images=image_refs,  # Image references as strings
                    metadata={
                        "layout": page.layout or {},
                        "text_length": len(page.text or ""),
                        "structured_data": page.structuredData or {},
                    },
                )
            )

        processing_time = time.time() - start_time

        return ParseResult(
            provider="llamaindex",
            total_pages=len(pages),
            pages=pages,
            raw_response={
                "job_id": getattr(result, "job_id", None),
                "total_pages": len(pages),
            },
            processing_time=processing_time,
            usage={
                "parse_mode": self.parse_mode,
                "model": self.model,
                "num_pages": len(pages),
            },
        )
