"""
HTML to PDF converter for PolicyQA privacy policy documents.

Converts HTML files to PDF preserving full document structure using Playwright.
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def convert_html_to_pdf(
    html_path: Path,
    output_dir: Path,
    filename: Optional[str] = None
) -> Optional[Path]:
    """
    Convert HTML file to PDF using Playwright (preserves full document rendering).

    Args:
        html_path: Path to input HTML file
        output_dir: Directory to save PDF
        filename: Optional PDF filename (default: same as HTML with .pdf extension)

    Returns:
        Path to generated PDF file, or None if conversion failed
    """
    try:
        from playwright.sync_api import sync_playwright

        if not html_path.exists():
            logger.error(f"HTML file not found: {html_path}")
            return None

        # Create output directory if needed
        output_dir.mkdir(parents=True, exist_ok=True)

        # Determine output filename
        if filename is None:
            filename = html_path.stem + '.pdf'

        pdf_path = output_dir / filename

        # Convert HTML to PDF using Playwright
        logger.debug(f"Converting {html_path.name} to PDF with Playwright...")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Load HTML file
            html_url = f"file://{html_path.absolute()}"
            page.goto(html_url, wait_until='networkidle')

            # Save as PDF
            page.pdf(
                path=str(pdf_path),
                format='Letter',
                print_background=True,
                margin={'top': '0.5in', 'right': '0.5in', 'bottom': '0.5in', 'left': '0.5in'}
            )

            browser.close()

        logger.debug(f"Successfully created PDF: {pdf_path}")
        return pdf_path

    except ImportError:
        logger.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
        return None
    except Exception as e:
        logger.error(f"Failed to convert {html_path} to PDF: {e}")
        return None


def find_policy_html(
    website: str,
    original_dir: Path,
    sanitized_dir: Path
) -> Optional[Path]:
    """
    Find HTML policy file for a website.

    Searches for matching HTML file using various patterns:
    - {number}_www.{website}.html (original_policies)
    - {number}_{website}.html (sanitized_policies)

    Args:
        website: Website domain (e.g., "ticketmaster.com")
        original_dir: Directory with original_policies
        sanitized_dir: Directory with sanitized_policies

    Returns:
        Path to HTML file (prefer original, fallback to sanitized), or None if not found
    """
    # Search patterns (prefer original policies)
    search_patterns = [
        (original_dir, f"*_www.{website}.html"),
        (original_dir, f"*_{website}.html"),
        (sanitized_dir, f"*_{website}.html"),
        (sanitized_dir, f"*_www.{website}.html"),
    ]

    for directory, pattern in search_patterns:
        if not directory.exists():
            continue

        matches = list(directory.glob(pattern))
        if matches:
            logger.debug(f"Found HTML for {website}: {matches[0].name}")
            return matches[0]

    logger.warning(f"No HTML file found for website: {website}")
    return None
