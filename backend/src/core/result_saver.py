"""
Result saver - handles all file I/O for benchmark results.

File structure:
data/results/
└── run_{timestamp}/
    ├── config.json
    ├── docs/
    │   ├── {doc_id}/
    │   │   ├── {provider}.json
    │   │   ├── aggregated.json
    │   │   └── doc.log
    ├── summary.json
    └── run.log

Thread-safety: Uses locks to ensure safe concurrent file writes.
"""

import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from src.core.schemas import ProviderResult, DocumentResult, RunSummary


class ResultSaver:
    """Saves benchmark results to structured files."""

    def __init__(self, output_dir: Path, run_id: str = None):
        """
        Initialize result saver with thread-safe file I/O.

        Args:
            output_dir: Base directory for results (e.g., data/results)
            run_id: Optional run ID (default: timestamp-based)
        """
        self.output_dir = Path(output_dir)

        # Thread-safe file I/O lock
        self._write_lock = threading.Lock()

        # Create run directory
        if run_id is None:
            run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.run_id = run_id
        self.run_dir = self.output_dir / run_id
        self.docs_dir = self.run_dir / "docs"

        # Create directories
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.docs_dir.mkdir(exist_ok=True)

        print(f"📁 Results directory: {self.run_dir}")

    def save_config(self, config: Dict[str, Any]):
        """Save run configuration (thread-safe)."""
        config_path = self.run_dir / "config.json"
        with self._write_lock:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)

    def save_provider_result(self, result: ProviderResult):
        """
        Save individual provider result (thread-safe).

        File: docs/{doc_id}/{provider}.json
        """
        with self._write_lock:
            doc_dir = self.docs_dir / result.doc_id
            doc_dir.mkdir(exist_ok=True)

            result_path = doc_dir / f"{result.provider}.json"
            with open(result_path, 'w') as f:
                json.dump(result.to_dict(), f, indent=2)

            print(f"   💾 Saved: {result_path.relative_to(self.output_dir)}")

    def save_document_aggregated(self, doc_result: DocumentResult):
        """
        Save aggregated document result (thread-safe).

        File: docs/{doc_id}/aggregated.json
        """
        with self._write_lock:
            doc_dir = self.docs_dir / doc_result.doc_id
            doc_dir.mkdir(exist_ok=True)

            result_path = doc_dir / "aggregated.json"
            with open(result_path, 'w') as f:
                json.dump(doc_result.to_dict(), f, indent=2)

            print(f"   💾 Saved: {result_path.relative_to(self.output_dir)}")

    def save_document_log(self, doc_id: str, log_content: str):
        """
        Save document log file (thread-safe).

        File: docs/{doc_id}/doc.log
        """
        with self._write_lock:
            doc_dir = self.docs_dir / doc_id
            doc_dir.mkdir(exist_ok=True)

            log_path = doc_dir / "doc.log"
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(log_content)

            print(f"   💾 Saved: {log_path.relative_to(self.output_dir)}")

    def save_run_summary(self, summary: RunSummary):
        """
        Save overall run summary (thread-safe).

        File: summary.json
        """
        with self._write_lock:
            summary_path = self.run_dir / "summary.json"
            with open(summary_path, 'w') as f:
                json.dump(summary.to_dict(), f, indent=2)

            print(f"\n📊 Run summary saved: {summary_path}")

    def load_doc_result(self, doc_id: str) -> Dict:
        """
        Load aggregated document result (for resume capability).

        Returns:
            DocumentResult dict if exists, else raises FileNotFoundError
        """
        aggregated_path = self.docs_dir / doc_id / "aggregated.json"

        if not aggregated_path.exists():
            raise FileNotFoundError(f"No saved result for document: {doc_id}")

        with open(aggregated_path) as f:
            data = json.load(f)

        return data

    def doc_completed(self, doc_id: str) -> bool:
        """Check if document has already been processed."""
        aggregated_path = self.docs_dir / doc_id / "aggregated.json"
        return aggregated_path.exists()
