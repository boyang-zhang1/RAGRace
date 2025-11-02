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
    DatasetPerformanceSummary,
    ProviderPerformance,
    ProviderDetailResponse,
    ProviderDocumentDetail,
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


@router.get("/datasets/{dataset_name}/documents", response_model=RunDetail)
async def get_dataset_documents(dataset_name: str, db=Depends(get_db)):
    """
    Get all documents and Q&A results for a dataset across all runs.

    This endpoint aggregates document-level results across ALL completed runs:
    - For each (document, provider) pair, uses the LATEST successful run's result
    - Includes all question results (Q&A) for each provider-document combination
    - Returns structure identical to RunDetail for component reuse

    Path parameters:
    - dataset_name: Dataset identifier (e.g., 'qasper', 'squad2')

    Returns:
    Document-level breakdown with provider Q&A results, similar to run details.
    """
    # First, get the latest ProviderResult IDs per (document, provider) using raw SQL
    # This is more efficient than fetching all and filtering in Python
    latest_pr_ids_query = """
    WITH latest_results AS (
        SELECT DISTINCT ON (pr.document_id, pr.provider)
            pr.id as provider_result_id
        FROM provider_results pr
        JOIN benchmark_runs br ON pr.run_id = br.id
        WHERE br.dataset_name = $1
          AND br.status = 'COMPLETED'
          AND pr.status = 'SUCCESS'
        ORDER BY pr.document_id, pr.provider, br.completed_at DESC NULLS LAST, pr.created_at DESC
    )
    SELECT provider_result_id FROM latest_results;
    """

    latest_pr_ids_raw = await prisma.query_raw(latest_pr_ids_query, dataset_name)

    if not latest_pr_ids_raw:
        # No results found for this dataset
        raise HTTPException(
            status_code=404,
            detail=f"No completed benchmark results found for dataset '{dataset_name}'"
        )

    # Extract IDs
    provider_result_ids = [row["provider_result_id"] for row in latest_pr_ids_raw]

    # Now fetch the full ProviderResult objects with all related data
    provider_results = await prisma.providerresult.find_many(
        where={"id": {"in": provider_result_ids}},
        include={
            "document": True,
            "questionResults": {"include": {"question": True}},
        },
    )

    if not provider_results:
        raise HTTPException(
            status_code=404,
            detail=f"No results found for dataset '{dataset_name}'"
        )

    # Group results by document (same logic as run details)
    docs_map = {}
    all_providers = set()

    for pr in provider_results:
        doc = pr.document
        doc_id = doc.docId
        all_providers.add(pr.provider)

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

    # Build response (reusing RunDetail structure for component compatibility)
    return RunDetail(
        run_id=f"dataset_{dataset_name}",  # Synthetic run_id for consistency
        dataset=dataset_name,
        split="all",  # Aggregated across all splits
        providers=sorted(list(all_providers)),
        status="completed",
        num_docs=len(documents),
        num_questions=sum(
            len(qr)
            for doc in documents
            for pr in doc.providers.values()
            for qr in [pr.questions]
        ),
        config={},  # No specific config for aggregated view
        started_at=None,  # Not applicable for aggregated view
        completed_at=None,
        duration_seconds=None,
        error_message=None,
        documents=documents,
    )


@router.get("/datasets/{dataset_name}/performance", response_model=DatasetPerformanceSummary)
async def get_dataset_performance(dataset_name: str, db=Depends(get_db)):
    """
    Get aggregated provider performance for a dataset.

    This endpoint aggregates results across ALL runs and splits for the dataset:
    - For each (document, provider) pair, uses the LATEST run's result
    - Aggregates scores across all documents for each provider
    - Returns provider rankings and performance metrics

    Path parameters:
    - dataset_name: Dataset identifier (e.g., 'qasper', 'squad2')

    Returns:
    Aggregated performance summary with provider rankings.
    """
    # Use raw SQL to efficiently get latest SUCCESS ProviderResult per (documentId, provider) pair
    # Only include successful results - failed results are excluded from aggregation
    query = """
    WITH latest_results AS (
        SELECT DISTINCT ON (pr.document_id, pr.provider)
            pr.id,
            pr.run_id,
            pr.document_id,
            pr.provider,
            pr.status,
            pr.aggregated_scores,
            pr.duration_seconds,
            pr.created_at,
            br.completed_at
        FROM provider_results pr
        JOIN benchmark_runs br ON pr.run_id = br.id
        WHERE br.dataset_name = $1
          AND br.status = 'COMPLETED'
          AND pr.status = 'SUCCESS'
        ORDER BY pr.document_id, pr.provider, br.completed_at DESC NULLS LAST, pr.created_at DESC
    )
    SELECT * FROM latest_results
    ORDER BY provider, document_id;
    """

    results = await prisma.query_raw(query, dataset_name)

    if not results:
        # Return empty summary if no results found
        return DatasetPerformanceSummary(
            dataset_name=dataset_name,
            total_runs=0,
            total_documents=0,
            providers=[],
            last_run_date=None,
        )

    # Get metadata: total runs and last run date
    total_runs = await prisma.benchmarkrun.count(
        where={"datasetName": dataset_name, "status": "COMPLETED"}
    )

    latest_run = await prisma.benchmarkrun.find_first(
        where={"datasetName": dataset_name, "status": "COMPLETED"},
        order={"completedAt": "desc"}
    )
    last_run_date = latest_run.completedAt if latest_run else None

    # Count unique documents
    unique_docs = set(r["document_id"] for r in results)
    total_documents = len(unique_docs)

    # Group by provider and aggregate
    from collections import defaultdict
    import statistics

    provider_data = defaultdict(lambda: {
        "results": [],
        "durations": [],
        "run_ids": set(),
    })

    for row in results:
        provider = row["provider"]
        provider_data[provider]["results"].append({
            "scores": row["aggregated_scores"],
            "status": row["status"],
        })
        if row["duration_seconds"]:
            provider_data[provider]["durations"].append(row["duration_seconds"])
        provider_data[provider]["run_ids"].add(row["run_id"])

    # Build ProviderPerformance objects
    providers = []
    for provider_name, data in provider_data.items():
        # Aggregate scores across all documents
        all_scores = defaultdict(list)

        for result in data["results"]:
            # All results are SUCCESS (filtered by query)
            scores_dict = result["scores"]
            if isinstance(scores_dict, dict):
                for metric, value in scores_dict.items():
                    if isinstance(value, (int, float)):
                        all_scores[metric].append(value)

        # Calculate averages
        aggregated_scores = {
            metric: statistics.mean(values)
            for metric, values in all_scores.items()
        }

        avg_duration = statistics.mean(data["durations"]) if data["durations"] else None

        providers.append(ProviderPerformance(
            provider=provider_name,
            num_documents=len(data["results"]),
            num_runs=len(data["run_ids"]),
            aggregated_scores=aggregated_scores,
            avg_duration_seconds=avg_duration,
        ))

    # Sort providers by first available metric (or alphabetically)
    # Frontend will handle re-sorting based on selected metric
    providers.sort(key=lambda p: p.provider)

    return DatasetPerformanceSummary(
        dataset_name=dataset_name,
        total_runs=total_runs,
        total_documents=total_documents,
        providers=providers,
        last_run_date=last_run_date,
    )


@router.get("/datasets/{dataset_name}/providers/{provider_name}", response_model=ProviderDetailResponse)
async def get_provider_detail(dataset_name: str, provider_name: str, db=Depends(get_db)):
    """
    Get detailed document-level results for a specific provider on a dataset.

    Shows which documents and runs contributed to the aggregated performance.

    Path parameters:
    - dataset_name: Dataset identifier (e.g., 'qasper')
    - provider_name: Provider name (e.g., 'llamaindex')

    Returns:
    Document-level breakdown for the provider on this dataset.
    """
    # Get latest SUCCESS ProviderResult per document for this provider
    query = """
    WITH latest_results AS (
        SELECT DISTINCT ON (pr.document_id)
            pr.id,
            pr.run_id,
            pr.document_id,
            pr.provider,
            pr.status,
            pr.aggregated_scores,
            pr.duration_seconds,
            pr.created_at,
            br.completed_at,
            br.run_id as bench_run_id,
            d.doc_id,
            d.doc_title
        FROM provider_results pr
        JOIN benchmark_runs br ON pr.run_id = br.id
        JOIN documents d ON pr.document_id = d.id
        WHERE br.dataset_name = $1
          AND pr.provider = $2
          AND br.status = 'COMPLETED'
          AND pr.status = 'SUCCESS'
        ORDER BY pr.document_id, br.completed_at DESC NULLS LAST, pr.created_at DESC
    )
    SELECT * FROM latest_results
    ORDER BY bench_run_id DESC, doc_id;
    """

    results = await prisma.query_raw(query, dataset_name, provider_name)

    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No results found for provider '{provider_name}' on dataset '{dataset_name}'"
        )

    # Build document details
    documents = []
    all_scores = defaultdict(list)
    unique_runs = set()

    for row in results:
        documents.append(ProviderDocumentDetail(
            doc_id=row["doc_id"],
            doc_title=row["doc_title"],
            run_id=row["bench_run_id"],
            run_date=row["completed_at"],
            aggregated_scores=row["aggregated_scores"],
            duration_seconds=row["duration_seconds"],
            status=row["status"].lower(),
        ))
        unique_runs.add(row["bench_run_id"])

        # Collect scores for overall aggregation
        if isinstance(row["aggregated_scores"], dict):
            for metric, value in row["aggregated_scores"].items():
                if isinstance(value, (int, float)):
                    all_scores[metric].append(value)

    # Calculate overall scores
    import statistics
    overall_scores = {
        metric: statistics.mean(values)
        for metric, values in all_scores.items()
    }

    return ProviderDetailResponse(
        dataset_name=dataset_name,
        provider=provider_name,
        total_documents=len(documents),
        total_runs=len(unique_runs),
        overall_scores=overall_scores,
        documents=documents,
    )
