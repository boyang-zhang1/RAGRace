"""
Simple PDF generator for converting text to PDF files.

Used for testing document-based RAG providers (LandingAI, Reducto)
with text-based datasets like SQuAD.
"""

from pathlib import Path
from typing import Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT


def text_to_pdf(
    text: str,
    output_path: str,
    title: Optional[str] = None,
    author: Optional[str] = None
) -> Path:
    """
    Convert plain text to a simple PDF file.

    Args:
        text: The text content to convert
        output_path: Path where PDF will be saved
        title: Optional document title
        author: Optional document author

    Returns:
        Path to the created PDF file
    """
    # Create output directory if needed
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Create PDF document
    doc = SimpleDocTemplate(
        str(output_file),
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch,
    )

    # Set metadata
    if title:
        doc.title = title
    if author:
        doc.author = author

    # Build content
    story = []
    styles = getSampleStyleSheet()

    # Add title if provided
    if title:
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            alignment=TA_LEFT
        )
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 0.2 * inch))

    # Add main text content
    # Split into paragraphs for better formatting
    paragraphs = text.split('\n\n')
    if not paragraphs or paragraphs == ['']:
        # If no paragraph breaks, treat as single paragraph
        paragraphs = [text]

    body_style = styles['BodyText']
    for para_text in paragraphs:
        if para_text.strip():  # Skip empty paragraphs
            # Escape special characters for reportlab
            para_text = para_text.replace('&', '&amp;')
            para_text = para_text.replace('<', '&lt;')
            para_text = para_text.replace('>', '&gt;')

            para = Paragraph(para_text, body_style)
            story.append(para)
            story.append(Spacer(1, 0.1 * inch))

    # Build PDF
    doc.build(story)

    return output_file


def squad_context_to_pdf(
    context: str,
    output_path: str,
    title: str = "Document"
) -> Path:
    """
    Convert a SQuAD context paragraph to PDF.

    Convenience function for creating PDFs from SQuAD dataset contexts.

    Args:
        context: The SQuAD context text
        output_path: Path where PDF will be saved
        title: Document title (default: "Document")

    Returns:
        Path to the created PDF file
    """
    return text_to_pdf(
        text=context,
        output_path=output_path,
        title=title,
        author="SQuAD Dataset"
    )
