"""
RAG Logger - Comprehensive file logging for RAGRace tests.

Logs all RAG operations to file for debugging and analysis:
- Document metadata (PDF name, path, size, title)
- Questions (full text, not truncated)
- Ground truth answers (full text)
- Provider responses (complete answers, all chunks, scores)
- Evaluation metrics (per-question and aggregated)
"""

import logging
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class RAGLogger:
    """
    Comprehensive logger for RAG operations.

    Creates detailed log files in data/results/ with:
    - Human-readable format
    - Complete data (no truncation)
    - Structured sections for easy parsing
    - Thread-safe logging (uses threading.Lock)
    """

    def __init__(self, log_dir: str = "data/results", test_name: str = "ragrace"):
        """
        Initialize RAG logger.

        Args:
            log_dir: Directory for log files
            test_name: Name of the test (used in filename)
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create timestamped log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"{test_name}_{timestamp}.log"

        # Thread safety lock
        self._lock = threading.Lock()

        # Set up file handler
        self.logger = logging.getLogger(f"RAGLogger_{timestamp}")
        self.logger.setLevel(logging.INFO)

        # Remove any existing handlers
        self.logger.handlers = []

        # File handler
        file_handler = logging.FileHandler(self.log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        # Format: plain text (no timestamps in file, we have sections)
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)

        # Write header
        self.log_section("RAGRACE TEST LOG")
        self.log(f"Timestamp: {datetime.now().isoformat()}")
        self.log(f"Log file: {self.log_file}")
        self.log("")

    def log_section(self, title: str, level: int = 1):
        """
        Log a section header.

        Args:
            title: Section title
            level: Header level (1=major, 2=minor, 3=sub)
        """
        with self._lock:
            if level == 1:
                self.logger.info("=" * 80)
                self.logger.info(f" {title}")
                self.logger.info("=" * 80)
            elif level == 2:
                self.logger.info("-" * 80)
                self.logger.info(f" {title}")
                self.logger.info("-" * 80)
            else:
                self.logger.info(f"\n### {title}")

    def log(self, message: str):
        """Log a message (thread-safe)."""
        with self._lock:
            self.logger.info(message)

    def log_document(self, doc_id: str, doc_title: str, pdf_path: str,
                     pdf_size: int, num_questions: int, metadata: Optional[Dict] = None):
        """
        Log document information.

        Args:
            doc_id: Document identifier (e.g., arxiv ID)
            doc_title: Full document title
            pdf_path: Path to PDF file
            pdf_size: PDF file size in bytes
            num_questions: Number of questions for this document
            metadata: Additional metadata
        """
        self.log_section(f"DOCUMENT: {doc_id}", level=2)
        self.log(f"ID: {doc_id}")
        self.log(f"Title: {doc_title}")
        self.log(f"PDF Path: {pdf_path}")
        self.log(f"PDF Size: {pdf_size:,} bytes ({pdf_size / 1024 / 1024:.2f} MB)")
        self.log(f"Questions: {num_questions}")

        if metadata:
            self.log("\nMetadata:")
            for key, value in metadata.items():
                self.log(f"  {key}: {value}")
        self.log("")

    def log_question(self, question_num: int, question: str, ground_truth: str,
                      question_id: Optional[str] = None):
        """
        Log question and ground truth.

        Args:
            question_num: Question number
            question: Full question text
            ground_truth: Full ground truth answer
            question_id: Optional question identifier
        """
        self.log_section(f"Question {question_num}", level=3)
        if question_id:
            self.log(f"Question ID: {question_id}")
        self.log(f"Question: {question}")
        self.log(f"\nGround Truth:\n{ground_truth}")
        self.log("")

    def log_provider_response(self, provider_name: str, answer: str,
                               context_chunks: List[str], latency_ms: float,
                               metadata: Optional[Dict] = None):
        """
        Log provider response with full details.

        Args:
            provider_name: Name of the RAG provider
            answer: Complete answer (not truncated)
            context_chunks: All retrieved context chunks
            latency_ms: Query latency in milliseconds
            metadata: Additional metadata (scores, etc.)
        """
        self.log(f">>> {provider_name} Response:")
        self.log(f"Latency: {latency_ms:.0f}ms")
        self.log(f"Chunks Retrieved: {len(context_chunks)}")

        if metadata:
            # Log similarity scores if available
            if 'similarity_scores' in metadata:
                scores = metadata['similarity_scores']
                self.log(f"Similarity Scores: {[f'{s:.4f}' for s in scores]}")
            if 'avg_similarity_score' in metadata:
                self.log(f"Avg Similarity: {metadata['avg_similarity_score']:.4f}")

        self.log(f"\nAnswer:\n{answer}")

        self.log(f"\nRetrieved Chunks ({len(context_chunks)}):")
        for i, chunk in enumerate(context_chunks, 1):
            self.log(f"\n[Chunk {i}]")
            self.log(chunk[:500] + ("..." if len(chunk) > 500 else ""))

        self.log("")

    def log_evaluation_result(self, provider_name: str, question_num: int,
                               metrics: Dict[str, float]):
        """
        Log evaluation metrics for a single question.

        Args:
            provider_name: Name of the RAG provider
            question_num: Question number
            metrics: Metric scores (e.g., {'faithfulness': 0.85, ...})
        """
        self.log(f"[Eval] {provider_name} - Q{question_num}:")
        for metric, score in metrics.items():
            self.log(f"  {metric}: {score:.4f}")

    def log_aggregated_scores(self, provider_scores: Dict[str, Dict[str, float]]):
        """
        Log aggregated scores for all providers.

        Args:
            provider_scores: {provider_name: {metric: score, ...}, ...}
        """
        self.log_section("AGGREGATED EVALUATION SCORES", level=1)

        for provider_name, scores in provider_scores.items():
            self.log(f"\n{provider_name}:")
            for metric, score in scores.items():
                self.log(f"  {metric}: {score:.4f}")

        self.log("")

    def log_winner(self, winner: str, winner_counts: Dict[str, int],
                    total_metrics: int):
        """
        Log the final winner.

        Args:
            winner: Name of the winning provider
            winner_counts: {provider_name: num_metrics_won, ...}
            total_metrics: Total number of metrics
        """
        self.log_section("FINAL RESULTS", level=1)
        self.log(f"🏆 WINNER: {winner}")
        self.log(f"   Won {winner_counts[winner]}/{total_metrics} metrics")
        self.log("\nMedal Count:")
        for provider, count in sorted(winner_counts.items(),
                                      key=lambda x: x[1], reverse=True):
            medals = "🥇" * count
            self.log(f"  {provider}: {count} {medals}")
        self.log("")

    def log_json(self, data: Dict[str, Any], title: str = "Data"):
        """
        Log data as formatted JSON.

        Args:
            data: Data to log
            title: Section title
        """
        self.log_section(title, level=3)
        self.log(json.dumps(data, indent=2))
        self.log("")

    def close(self):
        """Close the logger and finalize the log file."""
        self.log_section("END OF LOG", level=1)
        self.log(f"Log file saved to: {self.log_file}")

        # Close handlers
        for handler in self.logger.handlers:
            handler.close()

        print(f"\n📝 Detailed log saved to: {self.log_file}")
