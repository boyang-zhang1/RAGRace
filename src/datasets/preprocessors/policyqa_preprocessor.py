"""
PolicyQA dataset preprocessor.

Converts privacy policy HTML documents to PDF and extracts question-context-answer
triples in standardized format for RAG evaluation.
"""

import json
import logging
from typing import Optional
from pathlib import Path
from collections import defaultdict

from .base import BasePreprocessor, DatasetSample, ProcessedDataset
from ..downloaders.policyqa_downloader import PolicyQADownloader
from src.utils.html_to_pdf import convert_html_to_pdf, find_policy_html

logger = logging.getLogger(__name__)


class PolicyQAPreprocessor(BasePreprocessor):
    """
    Preprocessor for PolicyQA dataset (privacy policy QA).

    Converts HTML privacy policy documents to PDF format for RAG providers.
    Groups questions by website/document (not by paragraph).
    """

    def __init__(self, cache_dir: str = "data/datasets/PolicyQA"):
        """
        Initialize PolicyQA preprocessor.

        Args:
            cache_dir: Directory to cache downloaded JSON files and PDFs
        """
        self.downloader = PolicyQADownloader(cache_dir=cache_dir)
        self.cache_dir = Path(cache_dir)
        self.pdf_cache_dir = self.cache_dir / "pdfs"
        self.original_policies_dir = self.cache_dir / "original_policies"
        self.sanitized_policies_dir = self.cache_dir / "sanitized_policies"

    def _extract_pdf_text(self, pdf_path: Path) -> Optional[str]:
        """
        Extract raw text from PDF using pypdf.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Raw text from PDF, or None if extraction failed
        """
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(pdf_path))
            text_parts = []

            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            full_text = "\n\n".join(text_parts)
            return full_text if full_text.strip() else None

        except Exception as e:
            logger.warning(f"Failed to extract text from {pdf_path}: {e}")
            return None

    def process(
        self,
        file_path: Optional[str] = None,
        split: str = "train",
        max_docs: Optional[int] = None,
        max_questions_per_doc: Optional[int] = None,
        max_samples: Optional[int] = None,
        **kwargs
    ) -> ProcessedDataset:
        """
        Process PolicyQA dataset.

        Converts HTML privacy policies to PDF, groups questions by document.

        Args:
            file_path: Path to PolicyQA JSON file (if None, will download from GitHub)
            split: Dataset split ('train', 'dev', or 'test')
            max_docs: Maximum number of documents/websites to process (None = all)
            max_questions_per_doc: Maximum questions per document (None = all)
            max_samples: Legacy parameter for total samples (use max_docs instead)

        Returns:
            ProcessedDataset with samples containing pdf_path in metadata
        """
        # Download file if not provided
        if file_path is None:
            logger.info(f"Downloading PolicyQA {split} split from GitHub...")
            downloaded_path = self.downloader.download(split)
            if downloaded_path is None:
                raise RuntimeError(f"Failed to download PolicyQA {split} split")
            file_path = str(downloaded_path)
        else:
            if not Path(file_path).exists():
                raise FileNotFoundError(f"PolicyQA file not found: {file_path}")

        logger.info(f"Processing PolicyQA dataset from {file_path}")

        # Load JSON
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Group questions by website (each website = one document)
        website_data_map = {}
        for website_data in data['data']:
            website_title = website_data['title']
            website_data_map[website_title] = website_data

        stats = {
            'total_websites': len(website_data_map),
            'pdfs_created': 0,
            'pdfs_cached': 0,
            'failed_conversions': 0,
            'total_questions': 0,
            'samples_created': 0
        }

        samples = []
        docs_processed = 0

        # Process each website (document) - limit by max_docs
        for website_title, website_data in website_data_map.items():
            # Check if we've processed enough documents
            if max_docs and docs_processed >= max_docs:
                logger.info(f"Reached max_docs limit ({max_docs}), stopping")
                break

            # Find HTML file and convert to PDF
            html_path = find_policy_html(
                website_title,
                self.original_policies_dir,
                self.sanitized_policies_dir
            )

            if html_path is None:
                logger.warning(f"Skipping {website_title}: HTML file not found")
                stats['failed_conversions'] += 1
                continue

            # Convert HTML to PDF (with caching)
            pdf_filename = f"{html_path.stem}.pdf"
            pdf_path = self.pdf_cache_dir / pdf_filename

            if pdf_path.exists():
                logger.debug(f"Using cached PDF for {website_title}")
                stats['pdfs_cached'] += 1
            else:
                logger.info(f"Converting {website_title} HTML to PDF...")
                pdf_path = convert_html_to_pdf(html_path, self.pdf_cache_dir, pdf_filename)
                if pdf_path is None:
                    logger.warning(f"Skipping {website_title}: PDF conversion failed")
                    stats['failed_conversions'] += 1
                    continue
                stats['pdfs_created'] += 1

            # Extract text from PDF for context
            pdf_text = self._extract_pdf_text(pdf_path)
            if pdf_text is None:
                logger.warning(f"Skipping {website_title}: PDF text extraction failed")
                stats['failed_conversions'] += 1
                continue

            # Successfully processed this document
            docs_processed += 1

            # Create doc_id for this website
            doc_id = website_title.replace('.', '_')

            # Process questions for this website (limit by max_questions_per_doc)
            questions_for_this_doc = 0
            for paragraph in website_data['paragraphs']:
                for qa in paragraph['qas']:
                    # Check per-document question limit
                    if max_questions_per_doc and questions_for_this_doc >= max_questions_per_doc:
                        break

                    stats['total_questions'] += 1

                    # Extract ground truth answer
                    if qa['answers']:
                        ground_truth = qa['answers'][0]['text']
                    else:
                        ground_truth = ""
                        logger.warning(f"Question {qa['id']} has no answers")

                    # Create sample with PDF metadata (like Qasper)
                    sample = DatasetSample(
                        question=qa['question'],
                        context=pdf_text,  # Full PDF text (not just paragraph)
                        ground_truth=ground_truth,
                        metadata={
                            'question_id': qa['id'],
                            'doc_id': doc_id,
                            'doc_title': website_title,
                            'pdf_path': str(pdf_path)  # CRITICAL: RAG providers need this
                        }
                    )
                    samples.append(sample)
                    stats['samples_created'] += 1
                    questions_for_this_doc += 1

                # Check per-document question limit
                if max_questions_per_doc and questions_for_this_doc >= max_questions_per_doc:
                    break

        # Create dataset metadata
        dataset_metadata = {
            'dataset': 'PolicyQA',
            'version': data.get('version', 'v1.0'),
            'split': split,
            **stats,
            'max_samples': max_samples
        }

        logger.info(
            f"PolicyQA processing complete: {stats['samples_created']} samples from "
            f"{stats['total_websites']} websites ({stats['pdfs_created']} PDFs created, "
            f"{stats['pdfs_cached']} cached, {stats['failed_conversions']} failed)"
        )

        return ProcessedDataset(
            samples=samples,
            dataset_name='PolicyQA',
            metadata=dataset_metadata
        )
