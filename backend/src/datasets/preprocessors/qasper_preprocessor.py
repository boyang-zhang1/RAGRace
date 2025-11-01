"""
Qasper dataset preprocessor.

Loads Qasper dataset from HuggingFace, downloads PDFs from arxiv,
and extracts raw text for realistic RAG evaluation.
"""

import logging
import requests
from typing import Optional
from pathlib import Path
from datasets import load_dataset

from .base import BasePreprocessor, DatasetSample, ProcessedDataset
from ..downloaders.arxiv_downloader import ArxivDownloader

logger = logging.getLogger(__name__)


class QasperPreprocessor(BasePreprocessor):
    """
    Preprocessor for Qasper dataset (Question Answering on Scholarly Publications).

    Approach:
    1. Load metadata from HuggingFace datasets (document IDs, questions, answers)
    2. Download original PDFs from arxiv (realistic RAG test with formatting artifacts)
    3. Extract raw text from PDFs (no cleaning - RAG should handle messy text)
    4. Create samples: question + raw_pdf_text + ground_truth_answer
    """

    def __init__(self, cache_dir: str = "data/datasets/Qasper/pdfs"):
        """
        Initialize Qasper preprocessor.

        Args:
            cache_dir: Directory to cache downloaded PDFs
        """
        self.downloader = ArxivDownloader(cache_dir=cache_dir)

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

    def _extract_answer(self, answer_dict: dict) -> str:
        """
        Extract answer text from Qasper answer structure.

        Qasper structure:
        answer_dict = {
            'answer': [
                {'unanswerable': bool, 'free_form_answer': str, ...},  # annotator 1
                {'unanswerable': bool, 'free_form_answer': str, ...},  # annotator 2
            ],
            'annotation_id': [...],
            'worker_id': [...]
        }

        Args:
            answer_dict: Qasper answer dictionary for one question

        Returns:
            Answer string (empty if unanswerable)
        """
        # Get list of answers from different annotators
        answers_list = answer_dict.get('answer', [])

        if not answers_list or len(answers_list) == 0:
            return ""

        # Use first annotator's answer
        first_annotator = answers_list[0]

        # Check if unanswerable
        if first_annotator.get('unanswerable', False):
            return ""

        # Extract answer text (try free_form_answer first)
        answer_text = first_annotator.get('free_form_answer', '').strip()

        # Fallback to extractive_spans if no free_form_answer
        if not answer_text:
            extractive_spans = first_annotator.get('extractive_spans', [])
            if extractive_spans:
                answer_text = ' '.join(extractive_spans)

        return answer_text

    def process(
        self,
        file_path: str = None,
        split: str = "train",
        max_docs: Optional[int] = None,
        filter_unanswerable: bool = True,
        **kwargs
    ) -> ProcessedDataset:
        """
        Process Qasper dataset.

        Args:
            file_path: Ignored (kept for interface compatibility)
            split: Dataset split ('train', 'validation', or 'test')
            max_docs: Maximum number of documents to process (None = all documents)
            filter_unanswerable: Skip questions with no answer

        Returns:
            ProcessedDataset with samples from successfully downloaded documents
        """
        logger.info(f"Loading Qasper dataset (split: {split})")

        # Download parquet file from HuggingFace API
        # (dataset scripts no longer supported, must use parquet directly)
        cache_dir = Path("data/datasets/Qasper/cache")
        cache_dir.mkdir(parents=True, exist_ok=True)
        parquet_cache = cache_dir / f"{split}.parquet"

        if not parquet_cache.exists():
            logger.info(f"Downloading Qasper {split} split from HuggingFace API...")
            api_url = f"https://huggingface.co/api/datasets/allenai/qasper/parquet/qasper/{split}/0.parquet"
            response = requests.get(api_url, stream=True)
            response.raise_for_status()

            with open(parquet_cache, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"Downloaded and cached to {parquet_cache}")
        else:
            logger.info(f"Using cached parquet file: {parquet_cache}")

        # Load dataset from cached parquet file
        dataset = load_dataset("parquet", data_files=str(parquet_cache), split="train")

        samples = []
        stats = {
            'total_docs': 0,
            'downloaded_docs': 0,
            'failed_downloads': 0,
            'total_questions': 0,
            'skipped_unanswerable': 0,
            'samples_created': 0
        }

        # Process documents
        docs_to_process = min(len(dataset), max_docs) if max_docs else len(dataset)
        logger.info(f"Processing {docs_to_process} documents from {len(dataset)} total")

        for i, doc_data in enumerate(dataset):
            if max_docs and i >= max_docs:
                break

            stats['total_docs'] += 1
            arxiv_id = doc_data['id']
            title = doc_data['title']

            logger.info(f"[{i+1}/{docs_to_process}] Processing document: {arxiv_id}")

            # Download PDF from arxiv
            pdf_path = self.downloader.download(arxiv_id)
            if pdf_path is None:
                logger.warning(f"Failed to download document {arxiv_id}, skipping")
                stats['failed_downloads'] += 1
                continue

            # Extract raw text from PDF
            pdf_text = self._extract_pdf_text(pdf_path)
            if pdf_text is None:
                logger.warning(f"Failed to extract text from {arxiv_id}, skipping")
                stats['failed_downloads'] += 1
                continue

            stats['downloaded_docs'] += 1

            # Process questions for this document
            qas = doc_data['qas']
            questions = qas['question']
            question_ids = qas['question_id']
            answers_list = qas['answers']

            # Create sample for each question
            for q_id, question, answer_dict in zip(question_ids, questions, answers_list):
                stats['total_questions'] += 1

                # Extract answer text
                answer = self._extract_answer(answer_dict)

                # Skip unanswerable if requested
                if filter_unanswerable and not answer:
                    stats['skipped_unanswerable'] += 1
                    continue

                # Create sample
                sample = DatasetSample(
                    question=question,
                    context=pdf_text,  # Raw PDF text - no preprocessing
                    ground_truth=answer,
                    metadata={
                        'question_id': q_id,
                        'doc_id': arxiv_id,
                        'doc_title': title,
                        'is_unanswerable': not bool(answer),
                        'pdf_path': str(pdf_path)
                    }
                )
                samples.append(sample)
                stats['samples_created'] += 1

        # Create dataset metadata
        dataset_metadata = {
            'dataset': 'Qasper',
            'split': split,
            **stats,
            'filter_unanswerable': filter_unanswerable
        }

        logger.info(
            f"Qasper processing complete: {stats['downloaded_docs']}/{stats['total_docs']} documents, "
            f"{stats['samples_created']} samples created"
        )

        return ProcessedDataset(
            samples=samples,
            dataset_name='Qasper',
            metadata=dataset_metadata
        )
