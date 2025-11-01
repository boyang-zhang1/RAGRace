"""Results API router - read-only endpoints for benchmark results."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from api.db import get_db, prisma
from api.models.responses import (
    RunSummary,
    RunDetail,
    DatasetInfo,
    ResultsListResponse,
    DocumentResult,
    ProviderResult,
    QuestionResult,
)

router = APIRouter()


@router.get("/results", response_model=ResultsListResponse)
async def list_results(
    dataset: Optional[str] = Query(None, description="Filter by dataset name"),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db=Depends(get_db),
):
    """
    List all completed benchmark runs.

    Query parameters:
    - dataset: Filter by dataset name (optional)
    - limit: Number of results (1-100, default: 20)
    - offset: Pagination offset (default: 0)

    Returns:
    List of benchmark runs with summary information.
    """
    # Build where clause
    where = {"status": "COMPLETED"}
    if dataset:
        where["datasetName"] = dataset

    # Query runs
    runs = await prisma.benchmarkrun.find_many(
        where=where,
        order={"completedAt": "desc"},
        skip=offset,
        take=limit,
    )

    # Count total
    total = await prisma.benchmarkrun.count(where=where)

    # Convert to response model
    run_summaries = [
        RunSummary(
            run_id=r.runId,
            dataset=r.datasetName,
            split=r.datasetSplit,
            providers=r.providers,
            status=r.status.lower(),
            num_docs=r.numDocs,
            num_questions=r.numQuestionsTotal,
            started_at=r.startedAt,
            completed_at=r.completedAt,
            duration_seconds=r.durationSeconds,
        )
        for r in runs
    ]

    return ResultsListResponse(
        runs=run_summaries,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/results/{run_id}", response_model=RunDetail)
async def get_run_details(run_id: str, db=Depends(get_db)):
    """
    Get full details for a specific benchmark run.

    Path parameters:
    - run_id: Unique run identifier (e.g., "run_20251030_163137")

    Returns:
    Complete run details including:
    - Run metadata and configuration
    - All documents processed
    - Results from each provider
    - All questions with answers and scores
    """
    # Query run with all related data
    run = await prisma.benchmarkrun.find_unique(
        where={"runId": run_id},
        include={
            "providerResults": {
                "include": {
                    "document": True,
                    "questionResults": {"include": {"question": True}},
                }
            }
        },
    )

    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    # Group results by document
    docs_map = {}

    for pr in run.providerResults:
        doc = pr.document
        doc_id = doc.docId

        # Create document entry if not exists
        if doc_id not in docs_map:
            docs_map[doc_id] = {
                "doc_id": doc_id,
                "doc_title": doc.docTitle,
                "providers": {},
            }

        # Build question results
        question_results = [
            QuestionResult(
                question_id=qr.question.questionId,
                question=qr.question.question,
                ground_truth=qr.question.groundTruth,
                response_answer=qr.responseAnswer,
                response_context=qr.responseContext,
                response_latency_ms=qr.responseLatencyMs,
                evaluation_scores=qr.evaluationScores,
            )
            for qr in pr.questionResults
        ]

        # Add provider result
        docs_map[doc_id]["providers"][pr.provider] = ProviderResult(
            provider=pr.provider,
            status=pr.status.lower(),
            error=pr.error,
            aggregated_scores=pr.aggregatedScores,
            duration_seconds=pr.durationSeconds,
            questions=question_results,
        )

    # Convert to DocumentResult list
    documents = [
        DocumentResult(
            doc_id=doc_data["doc_id"],
            doc_title=doc_data["doc_title"],
            providers=doc_data["providers"],
        )
        for doc_data in docs_map.values()
    ]

    # Build response
    return RunDetail(
        run_id=run.runId,
        dataset=run.datasetName,
        split=run.datasetSplit,
        providers=run.providers,
        status=run.status.lower(),
        num_docs=run.numDocs,
        num_questions=run.numQuestionsTotal,
        config=run.config,
        started_at=run.startedAt,
        completed_at=run.completedAt,
        duration_seconds=run.durationSeconds,
        error_message=run.errorMessage,
        documents=documents,
    )


@router.get("/datasets", response_model=List[DatasetInfo])
async def list_datasets():
    """
    Get list of available datasets.

    Returns:
    Static list of supported datasets with metadata.
    """
    datasets = [
        DatasetInfo(
            name="qasper",
            display_name="QASPER",
            description="Question Answering on Scientific Papers - NLP research papers with questions",
            available_splits=["train", "validation", "test"],
            num_documents=1585,
            task_type="question-answering",
        ),
        DatasetInfo(
            name="policyqa",
            display_name="PolicyQA",
            description="Question answering on insurance policy documents",
            available_splits=["train", "test"],
            num_documents=None,  # TODO: Add actual count
            task_type="question-answering",
        ),
        DatasetInfo(
            name="squad2",
            display_name="SQuAD 2.0",
            description="Stanford Question Answering Dataset with unanswerable questions",
            available_splits=["train", "validation"],
            num_documents=None,  # TODO: Add actual count
            task_type="question-answering",
        ),
    ]

    return datasets
