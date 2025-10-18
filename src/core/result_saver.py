"""
Result saver - handles all file I/O for benchmark results.

File structure:
data/results/
└── run_{timestamp}/
    ├── config.json
    ├── papers/
    │   ├── {paper_id}/
    │   │   ├── {provider}.json
    │   │   ├── aggregated.json
    │   │   └── paper.log
    ├── summary.json
    └── run.log
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from src.core.schemas import ProviderResult, PaperResult, RunSummary


class ResultSaver:
    """Saves benchmark results to structured files."""

    def __init__(self, output_dir: Path, run_id: str = None):
        """
        Initialize result saver.

        Args:
            output_dir: Base directory for results (e.g., data/results)
            run_id: Optional run ID (default: timestamp-based)
        """
        self.output_dir = Path(output_dir)

        # Create run directory
        if run_id is None:
            run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.run_id = run_id
        self.run_dir = self.output_dir / run_id
        self.papers_dir = self.run_dir / "papers"

        # Create directories
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.papers_dir.mkdir(exist_ok=True)

        print(f"📁 Results directory: {self.run_dir}")

    def save_config(self, config: Dict[str, Any]):
        """Save run configuration."""
        config_path = self.run_dir / "config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

    def save_provider_result(self, result: ProviderResult):
        """
        Save individual provider result.

        File: papers/{paper_id}/{provider}.json
        """
        paper_dir = self.papers_dir / result.paper_id
        paper_dir.mkdir(exist_ok=True)

        result_path = paper_dir / f"{result.provider}.json"
        with open(result_path, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)

        print(f"   💾 Saved: {result_path.relative_to(self.output_dir)}")

    def save_paper_aggregated(self, paper_result: PaperResult):
        """
        Save aggregated paper result.

        File: papers/{paper_id}/aggregated.json
        """
        paper_dir = self.papers_dir / paper_result.paper_id
        paper_dir.mkdir(exist_ok=True)

        result_path = paper_dir / "aggregated.json"
        with open(result_path, 'w') as f:
            json.dump(paper_result.to_dict(), f, indent=2)

        print(f"   💾 Saved: {result_path.relative_to(self.output_dir)}")

    def save_paper_log(self, paper_id: str, log_content: str):
        """
        Save paper log file.

        File: papers/{paper_id}/paper.log
        """
        paper_dir = self.papers_dir / paper_id
        paper_dir.mkdir(exist_ok=True)

        log_path = paper_dir / "paper.log"
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(log_content)

        print(f"   💾 Saved: {log_path.relative_to(self.output_dir)}")

    def save_run_summary(self, summary: RunSummary):
        """
        Save overall run summary.

        File: summary.json
        """
        summary_path = self.run_dir / "summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary.to_dict(), f, indent=2)

        print(f"\n📊 Run summary saved: {summary_path}")

    def load_paper_result(self, paper_id: str) -> Dict:
        """
        Load aggregated paper result (for resume capability).

        Returns:
            PaperResult dict if exists, else raises FileNotFoundError
        """
        aggregated_path = self.papers_dir / paper_id / "aggregated.json"

        if not aggregated_path.exists():
            raise FileNotFoundError(f"No saved result for paper: {paper_id}")

        with open(aggregated_path) as f:
            data = json.load(f)

        return data

    def paper_completed(self, paper_id: str) -> bool:
        """Check if paper has already been processed."""
        aggregated_path = self.papers_dir / paper_id / "aggregated.json"
        return aggregated_path.exists()
