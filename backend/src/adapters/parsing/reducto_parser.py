"""Reducto parsing adapter with chunk-to-page mapping."""

import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, List

from reducto import Reducto

from .base import BaseParseAdapter, PageResult, ParseResult


class ReductoParser(BaseParseAdapter):
    """Parser using Reducto API with semantic chunking."""

    def __init__(self, api_key: str | None = None):
        """
        Initialize Reducto parser.

        Args:
            api_key: API key for Reducto. If None, reads from REDUCTO_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("REDUCTO_API_KEY")
        if not self.api_key:
            raise ValueError("Reducto API key not provided")

        # Set API key in environment for Reducto client
        os.environ["REDUCTO_API_KEY"] = self.api_key

    async def parse_pdf(self, pdf_path: Path) -> ParseResult:
        """
        Parse PDF using Reducto and map chunks to pages.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            ParseResult with chunks mapped to pages
        """
        start_time = time.time()

        # Initialize Reducto client
        client = Reducto()

        # Upload file
        upload_response = client.upload(file=pdf_path)

        # Parse with optimal settings for structured content
        result = client.parse.run(
            input=upload_response,
            enhance={
                "agentic": [],
                "summarize_figures": True,  # Add AI summaries for figures
            },
            retrieval={
                "chunking": {"chunk_mode": "variable"},  # Semantic chunking
                "embedding_optimized": True,
                "filter_blocks": [],
            },
            formatting={
                "add_page_markers": True,  # Important for page mapping
                "table_output_format": "dynamic",  # Best table format
                "merge_tables": False,  # Keep tables separate
            },
            settings={
                "ocr_system": "standard",
                "timeout": 900,
            },
        )

        # Debug: Save raw result structure
        import json
        debug_file_raw = Path("/Users/zby/data/RAGRace/data/temp/reducto_raw_result.json")
        try:
            with open(debug_file_raw, 'w') as f:
                result_info = {
                    "result_type": str(type(result)),
                    "has_result_attr": hasattr(result, 'result'),
                }
                if hasattr(result, '__dict__'):
                    result_info["result_dict_keys"] = list(result.__dict__.keys())
                if isinstance(result, dict):
                    result_info["dict_keys"] = list(result.keys())
                    result_info["result_value"] = result[:500] if len(str(result)) > 500 else result
                else:
                    result_info["result_str"] = str(result)[:500]

                json.dump(result_info, f, indent=2, default=str)
        except Exception as e:
            print(f"Debug raw result save failed: {e}")

        # Extract chunks from result - handle Reducto ParseResponse object
        if hasattr(result, 'result'):
            # result is a ParseResponse object with a result attribute
            result_data = result.result
            if hasattr(result_data, 'chunks'):
                # result_data is a ResultFullResult object with chunks attribute
                chunks = result_data.chunks
            elif isinstance(result_data, dict):
                chunks = result_data.get("chunks", [])
            else:
                chunks = []
        else:
            result_data = result
            chunks = result_data.get("chunks", []) if isinstance(result_data, dict) else []

        # Map chunks to pages using block metadata
        pages = self._map_chunks_to_pages(chunks)

        processing_time = time.time() - start_time

        return ParseResult(
            provider="reducto",
            total_pages=len(pages),
            pages=pages,
            raw_response={
                "total_chunks": len(chunks),
            },
            processing_time=processing_time,
        )

    def _map_chunks_to_pages(self, chunks: List[Dict[str, Any]]) -> List[PageResult]:
        """
        Map Reducto chunks to pages using block metadata and construct proper markdown.

        Args:
            chunks: List of chunks from Reducto API

        Returns:
            List of PageResult objects with proper markdown from blocks
        """
        page_map: Dict[int, List[str]] = defaultdict(list)
        page_images: Dict[int, List[str]] = defaultdict(list)
        max_page = 0

        for chunk in chunks:
            # Convert Pydantic object to dict if needed
            if hasattr(chunk, '__dict__'):
                chunk_dict = chunk.__dict__
            elif isinstance(chunk, dict):
                chunk_dict = chunk
            else:
                continue

            # Extract blocks - this is where the real structured content is
            blocks = chunk_dict.get("blocks", [])
            if not blocks:
                continue

            # Process each block to build markdown
            for block in blocks:
                # Convert block to dict if it's a Pydantic object
                if hasattr(block, '__dict__'):
                    block_dict = block.__dict__
                elif isinstance(block, dict):
                    block_dict = block
                else:
                    continue

                # Get block type and content
                block_type = block_dict.get("type", "Text")
                content = block_dict.get("content", "")

                if not content or not content.strip():
                    continue

                # Get page number from bbox
                bbox = block_dict.get("bbox", {})
                if hasattr(bbox, '__dict__'):
                    bbox = bbox.__dict__
                page_num = bbox.get("page", 1) if isinstance(bbox, dict) else 1

                # Skip footer blocks
                if block_type == "Footer":
                    continue

                # Format content based on block type
                if block_type == "Section Header":
                    formatted = f"## {content}\n\n"
                elif block_type == "Table":
                    # Table content already in markdown format
                    formatted = f"{content}\n\n"
                elif block_type == "List Item":
                    formatted = f"{content}\n\n"
                elif block_type == "Text":
                    formatted = f"{content}\n\n"
                else:
                    # Unknown type, treat as text
                    formatted = f"{content}\n\n"

                # Add to page map
                if page_num > 0:  # Ignore negative page numbers
                    page_map[page_num].append(formatted)
                    max_page = max(max_page, page_num)

                # Extract image URLs if available
                if block_type == "Image":
                    image_url = block_dict.get("image_url") or block_dict.get("url")
                    if image_url:
                        page_images[page_num].append(image_url)

        # Ensure we have at least one page
        if not page_map:
            page_map[1] = ["*No content extracted from blocks*"]
            max_page = 1
        else:
            max_page = max(max_page, 1)

        # Convert to PageResult objects
        pages = []
        for page_num in range(1, max_page + 1):
            page_blocks = page_map.get(page_num, [])
            markdown = "".join(page_blocks) if page_blocks else "*No content on this page*"

            pages.append(
                PageResult(
                    page_number=page_num,
                    markdown=markdown.strip(),
                    images=page_images.get(page_num, []),
                    metadata={
                        "block_count": len(page_blocks),
                        "has_images": len(page_images.get(page_num, [])) > 0,
                    },
                )
            )

        return pages
