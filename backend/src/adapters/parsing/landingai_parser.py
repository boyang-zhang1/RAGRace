"""LandingAI parsing adapter."""

import os
import re
import time
from pathlib import Path
from typing import Dict, Any
from collections import defaultdict

from landingai_ade import LandingAIADE

from .base import BaseParseAdapter, PageResult, ParseResult


class LandingAIParser(BaseParseAdapter):
    """Parser using LandingAI's Vision Agent API."""

    def __init__(self, api_key: str):
        """
        Initialize LandingAI parser.

        Args:
            api_key: API key for LandingAI (required).

        Raises:
            ValueError: If api_key is empty or None.
        """
        if not api_key:
            raise ValueError("LandingAI API key is required")
        self.api_key = api_key

    def _normalize_markdown(self, markdown: str) -> str:
        """
        Post-process LandingAI markdown for fairer comparison with other providers.

        Improvements:
        1. Remove anchor tags that clutter the output
        2. Improve table structure with semantic HTML
        3. Normalize table headers to use <th> tags
        4. Add <thead> and <tbody> for proper table structure

        Args:
            markdown: Raw markdown from LandingAI

        Returns:
            Normalized markdown with improved structure
        """
        if not markdown:
            return markdown

        # 1. Remove anchor tags: <a id='...'></a>
        markdown = re.sub(r'<a id=["\'][\w\-]+["\']></a>\s*', '', markdown)

        # 2. Improve table structure
        # Find all tables and enhance them
        def enhance_table(match):
            table_content = match.group(0)

            # Extract table ID if present
            table_id_match = re.search(r'<table[^>]*id=["\']([^"\']+)["\'][^>]*>', table_content)
            table_id = f' id="{table_id_match.group(1)}"' if table_id_match else ''

            # Split into rows
            rows = re.findall(r'<tr[^>]*>.*?</tr>', table_content, re.DOTALL)

            if not rows:
                return table_content

            # First row becomes header (convert <td> to <th>)
            first_row = rows[0]
            header_row = re.sub(
                r'<td([^>]*)>(.*?)</td>',
                r'<th\1>\2</th>',
                first_row
            )

            # Build new table with proper structure
            enhanced = f'<table{table_id}>\n<thead>\n{header_row}\n</thead>\n<tbody>\n'
            enhanced += '\n'.join(rows[1:])
            enhanced += '\n</tbody>\n</table>'

            return enhanced

        markdown = re.sub(
            r'<table[^>]*>.*?</table>',
            enhance_table,
            markdown,
            flags=re.DOTALL
        )

        # 3. Remove "Page | N" markers (they're redundant - we track pages separately)
        markdown = re.sub(r'Page \| \d+\s*', '', markdown)

        # 4. Remove copyright notices that appear on every page
        markdown = re.sub(r'Copyright ©\d{4}[^\n]*\n*', '', markdown)

        # 5. Clean up excessive whitespace
        markdown = re.sub(r'\n\n\n+', '\n\n', markdown)
        markdown = markdown.strip()

        return markdown

    async def parse_pdf(self, pdf_path: Path) -> ParseResult:
        """
        Parse PDF using LandingAI with page-by-page splitting.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            ParseResult with markdown content per page
        """
        start_time = time.time()

        # Initialize LandingAI client
        client = LandingAIADE(apikey=self.api_key)

        # Parse the PDF using dpt-2 model
        parse_response = client.parse(
            document=pdf_path,
            model="dpt-2",
        )

        # Convert response to dict if it's not already
        if hasattr(parse_response, 'dict'):
            response_data = parse_response.dict()
        elif hasattr(parse_response, 'model_dump'):
            response_data = parse_response.model_dump()
        elif isinstance(parse_response, dict):
            response_data = parse_response
        else:
            # Try to convert to dict
            response_data = dict(parse_response)

        # Extract metadata
        metadata = response_data.get("metadata", {})
        total_pages = metadata.get("page_count", 1)

        # Group chunks by page number
        chunks = response_data.get("chunks", [])
        page_chunks = defaultdict(list)

        for chunk in chunks:
            grounding = chunk.get("grounding", {})
            # LandingAI uses 0-based page indexing, convert to 1-based
            page_num_api = grounding.get("page", 0)  # API returns 0, 1, 2...
            page_num = page_num_api + 1  # Convert to 1, 2, 3...
            page_chunks[page_num].append(chunk)

        # Create PageResult for each page
        pages = []
        for page_num in range(1, total_pages + 1):
            # Combine markdown from all chunks on this page
            chunks_on_page = page_chunks.get(page_num, [])
            markdown_parts = [chunk.get("markdown", "") for chunk in chunks_on_page]
            combined_markdown = "\n\n".join(filter(None, markdown_parts))

            # If no chunks for this page, use empty string
            if not combined_markdown and page_num not in page_chunks:
                combined_markdown = ""

            # Normalize/clean markdown for fairer comparison
            combined_markdown = self._normalize_markdown(combined_markdown)

            # Collect chunk metadata
            chunk_metadata = []
            for chunk in chunks_on_page:
                chunk_metadata.append({
                    "type": chunk.get("type"),
                    "id": chunk.get("id"),
                    "grounding": chunk.get("grounding"),
                })

            pages.append(
                PageResult(
                    page_number=page_num,
                    markdown=combined_markdown,
                    images=[],  # LandingAI doesn't provide separate image URLs
                    metadata={
                        "chunks": chunk_metadata,
                        "chunk_count": len(chunks_on_page),
                    },
                )
            )

        # Calculate processing time
        duration_ms = metadata.get("duration_ms", 0)
        # Use API's duration if available, otherwise use our measured time
        processing_time = duration_ms / 1000.0 if duration_ms else (time.time() - start_time)

        return ParseResult(
            provider="landingai",
            total_pages=total_pages,
            pages=pages,
            raw_response=response_data,
            processing_time=processing_time,
            usage={
                "num_pages": total_pages,
                "credits_per_page": 3,  # Fixed rate for LandingAI
                "total_credits": total_pages * 3,
            },
        )
