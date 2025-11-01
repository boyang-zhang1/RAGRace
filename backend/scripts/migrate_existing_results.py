#!/usr/bin/env python3
"""
Migration script to import existing benchmark results from data/results/ into Supabase database.

This script:
1. Reads all run directories from data/results/run_*/
2. Parses summary.json and config.json for each run
3. Imports data into Prisma/Supabase with proper structure:
   - BenchmarkRun
   - Document
   - Question
   - ProviderResult
   - QuestionResult
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from prisma import Prisma


async def migrate_run(prisma: Prisma, run_dir: Path) -> Dict[str, Any]:
    """Migrate a single benchmark run to the database."""

    run_id = run_dir.name
    print(f"\n{'='*80}")
    print(f"Migrating run: {run_id}")
    print(f"{'='*80}")

    # Load run data
    summary_path = run_dir / "summary.json"
    config_path = run_dir / "config.json"

    if not summary_path.exists():
        print(f"⚠️  Skipping {run_id}: No summary.json found")
        return {"status": "skipped", "reason": "no_summary"}

    with open(summary_path) as f:
        summary = json.load(f)

    with open(config_path) as f:
        config = json.load(f)

    # Extract benchmark configuration
    benchmark_config = config.get("benchmark", {})
    dataset_config = benchmark_config.get("dataset", {})

    # Parse timestamps from summary
    started_at = datetime.fromisoformat(summary.get("timestamp_start", summary.get("timestamp", datetime.now().isoformat())))
    completed_at = datetime.fromisoformat(summary.get("timestamp_end", started_at.isoformat())) if "timestamp_end" in summary else None

    # Calculate duration
    duration_seconds = summary.get("duration_seconds")
    if duration_seconds is None and completed_at and started_at:
        duration_seconds = (completed_at - started_at).total_seconds()

    # Create BenchmarkRun record
    print(f"Creating BenchmarkRun record...")
    benchmark_run = await prisma.benchmarkrun.upsert(
        where={"runId": run_id},
        data={
            "create": {
                "runId": run_id,
                "datasetName": dataset_config.get("name", summary.get("config", {}).get("benchmark", {}).get("dataset", {}).get("name", "unknown")),
                "datasetSplit": dataset_config.get("split", summary.get("config", {}).get("benchmark", {}).get("dataset", {}).get("split", "train")),
                "providers": summary.get("providers", []),
                "numDocs": summary.get("num_docs", 0),
                "numQuestionsTotal": summary.get("num_questions_total", 0),
                "status": "COMPLETED",
                "config": json.dumps(config),  # Serialize JSON for Prisma
                "durationSeconds": duration_seconds,
                "startedAt": started_at,
                "completedAt": completed_at,
            },
            "update": {},  # Don't update if exists
        }
    )
    print(f"✓ BenchmarkRun created: {benchmark_run.id}")

    # Process each document
    stats = {
        "documents": 0,
        "questions": 0,
        "provider_results": 0,
        "question_results": 0,
    }

    for doc_result in summary.get("results", []):
        doc_id = doc_result["doc_id"]
        doc_title = doc_result["doc_title"]
        dataset_name = benchmark_run.datasetName

        print(f"\n  Processing document: {doc_id}")

        # Upsert Document
        document = await prisma.document.upsert(
            where={
                "docId_datasetName": {
                    "docId": doc_id,
                    "datasetName": dataset_name,
                }
            },
            data={
                "create": {
                    "docId": doc_id,
                    "datasetName": dataset_name,
                    "docTitle": doc_title,
                    "pdfPath": None,  # Will be populated later if needed
                    "pdfUrl": None,
                    "pdfSizeBytes": None,
                    "metadata": json.dumps({}),
                },
                "update": {},  # Don't update if exists
            }
        )
        stats["documents"] += 1
        print(f"    ✓ Document: {document.id}")

        # Process each provider's results for this document
        for provider_name, provider_data in doc_result.get("providers", {}).items():
            print(f"      Processing provider: {provider_name}")

            # Parse timestamps
            provider_started = None
            provider_completed = None
            if "timestamp_start" in provider_data:
                provider_started = datetime.fromisoformat(provider_data["timestamp_start"])
            if "timestamp_end" in provider_data:
                provider_completed = datetime.fromisoformat(provider_data["timestamp_end"])

            # Create ProviderResult
            provider_result = await prisma.providerresult.create(
                data={
                    "runId": benchmark_run.id,
                    "documentId": document.id,
                    "provider": provider_name,
                    "status": "SUCCESS" if provider_data.get("status") == "success" else "ERROR",
                    "error": provider_data.get("error"),
                    "indexId": provider_data.get("index_id"),
                    "aggregatedScores": json.dumps(provider_data.get("aggregated_scores", {})),
                    "durationSeconds": provider_data.get("duration_seconds"),
                    "startedAt": provider_started,
                    "completedAt": provider_completed,
                }
            )
            stats["provider_results"] += 1
            print(f"        ✓ ProviderResult: {provider_result.id}")

            # Process questions for this provider
            for question_data in provider_data.get("questions", []):
                question_id = question_data["question_id"]

                # Upsert Question
                question = await prisma.question.upsert(
                    where={
                        "questionId_documentId": {
                            "questionId": question_id,
                            "documentId": document.id,
                        }
                    },
                    data={
                        "create": {
                            "questionId": question_id,
                            "documentId": document.id,
                            "question": question_data.get("question", ""),
                            "groundTruth": question_data.get("ground_truth", ""),
                            "metadata": json.dumps({}),
                        },
                        "update": {},  # Don't update if exists
                    }
                )
                stats["questions"] += 1

                # Create QuestionResult
                await prisma.questionresult.create(
                    data={
                        "providerResultId": provider_result.id,
                        "questionId": question.id,
                        "responseAnswer": question_data.get("response_answer", ""),
                        "responseContext": question_data.get("response_context", []),
                        "responseLatencyMs": question_data.get("response_latency_ms"),
                        "responseMetadata": json.dumps(question_data.get("response_metadata", {})),
                        "evaluationScores": json.dumps(question_data.get("evaluation_scores", {})),
                    }
                )
                stats["question_results"] += 1

            print(f"        ✓ {len(provider_data.get('questions', []))} QuestionResults")

    print(f"\n  Summary for {run_id}:")
    print(f"    Documents: {stats['documents']}")
    print(f"    Questions: {stats['questions']}")
    print(f"    ProviderResults: {stats['provider_results']}")
    print(f"    QuestionResults: {stats['question_results']}")

    return {"status": "success", "stats": stats}


async def main():
    """Main migration function."""

    print("="*80)
    print("RAGRace Benchmark Results Migration")
    print("="*80)

    # Initialize Prisma client
    prisma = Prisma()
    await prisma.connect()

    try:
        # Find all run directories
        results_dir = Path(__file__).parent.parent.parent / "data" / "results"
        run_dirs = sorted([d for d in results_dir.iterdir() if d.is_dir() and d.name.startswith("run_")])

        print(f"\nFound {len(run_dirs)} benchmark runs to migrate\n")

        # Migrate each run
        total_stats = {
            "runs_migrated": 0,
            "runs_skipped": 0,
            "runs_failed": 0,
            "total_documents": 0,
            "total_questions": 0,
            "total_provider_results": 0,
            "total_question_results": 0,
        }

        for run_dir in run_dirs:
            try:
                result = await migrate_run(prisma, run_dir)
                if result["status"] == "success":
                    total_stats["runs_migrated"] += 1
                    total_stats["total_documents"] += result["stats"]["documents"]
                    total_stats["total_questions"] += result["stats"]["questions"]
                    total_stats["total_provider_results"] += result["stats"]["provider_results"]
                    total_stats["total_question_results"] += result["stats"]["question_results"]
                elif result["status"] == "skipped":
                    total_stats["runs_skipped"] += 1
            except Exception as e:
                print(f"\n❌ Error migrating {run_dir.name}: {e}")
                import traceback
                traceback.print_exc()
                total_stats["runs_failed"] += 1

        # Print final summary
        print("\n" + "="*80)
        print("Migration Complete!")
        print("="*80)
        print(f"\nRuns migrated:         {total_stats['runs_migrated']}")
        print(f"Runs skipped:          {total_stats['runs_skipped']}")
        print(f"Runs failed:           {total_stats['runs_failed']}")
        print(f"\nTotal documents:       {total_stats['total_documents']}")
        print(f"Total questions:       {total_stats['total_questions']}")
        print(f"Total provider results: {total_stats['total_provider_results']}")
        print(f"Total question results: {total_stats['total_question_results']}")
        print()

    finally:
        await prisma.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
