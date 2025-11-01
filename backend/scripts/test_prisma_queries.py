#!/usr/bin/env python3
"""
Test script to verify Prisma queries and data integrity after migration.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from prisma import Prisma


async def main():
    """Test Prisma queries."""

    print("="*80)
    print("Testing Prisma Queries and Data Integrity")
    print("="*80)

    prisma = Prisma()
    await prisma.connect()

    try:
        # Test 1: Count benchmark runs
        print("\n1. Counting benchmark runs...")
        runs_count = await prisma.benchmarkrun.count()
        print(f"   ✓ Found {runs_count} benchmark runs")

        # Test 2: Query all runs
        print("\n2. Querying all benchmark runs...")
        runs = await prisma.benchmarkrun.find_many(
            order={'createdAt': 'desc'},
            take=5
        )
        print(f"   ✓ Retrieved {len(runs)} runs (showing top 5):")
        for run in runs:
            print(f"      - {run.runId}: {run.datasetName} ({run.status})")

        # Test 3: Count documents
        print("\n3. Counting documents...")
        docs_count = await prisma.document.count()
        print(f"   ✓ Found {docs_count} unique documents")

        # Test 4: Count questions
        print("\n4. Counting questions...")
        questions_count = await prisma.question.count()
        print(f"   ✓ Found {questions_count} unique questions")

        # Test 5: Count provider results
        print("\n5. Counting provider results...")
        provider_results_count = await prisma.providerresult.count()
        print(f"   ✓ Found {provider_results_count} provider results")

        # Test 6: Count question results
        print("\n6. Counting question results...")
        question_results_count = await prisma.questionresult.count()
        print(f"   ✓ Found {question_results_count} question results")

        # Test 7: Query with relations
        print("\n7. Testing nested query with relations...")
        run_with_relations = await prisma.benchmarkrun.find_first(
            where={'status': 'COMPLETED'},
            include={
                'providerResults': {
                    'include': {
                        'document': True,
                        'questionResults': {
                            'include': {
                                'question': True
                            }
                        }
                    }
                }
            }
        )

        if run_with_relations:
            print(f"   ✓ Successfully queried run: {run_with_relations.runId}")
            print(f"      - Provider results: {len(run_with_relations.providerResults)}")
            if run_with_relations.providerResults:
                pr = run_with_relations.providerResults[0]
                print(f"      - Sample provider: {pr.provider}")
                print(f"      - Document: {pr.document.docTitle[:50]}...")
                print(f"      - Question results: {len(pr.questionResults)}")

        # Test 8: Test aggregations
        print("\n8. Testing aggregations by provider...")
        providers = await prisma.providerresult.group_by(
            by=['provider'],
            count=True
        )
        print(f"   ✓ Results by provider:")
        for p in providers:
            print(f"      - {p['provider']}: {p['_count']} results")

        # Test 9: Test dataset distribution
        print("\n9. Testing dataset distribution...")
        datasets = await prisma.benchmarkrun.group_by(
            by=['datasetName'],
            count=True
        )
        print(f"   ✓ Runs by dataset:")
        for d in datasets:
            print(f"      - {d['datasetName']}: {d['_count']} runs")

        # Test 10: Verify JSON deserialization
        print("\n10. Testing JSON field deserialization...")
        result_with_json = await prisma.questionresult.find_first(
            where={'evaluationScores': {'not': '{}'}}
        )
        if result_with_json:
            import json
            # Prisma automatically deserializes JSON fields
            eval_scores = json.loads(result_with_json.evaluationScores) if isinstance(result_with_json.evaluationScores, str) else result_with_json.evaluationScores
            print(f"   ✓ Evaluation scores successfully deserialized:")
            for metric, score in list(eval_scores.items())[:3]:
                print(f"      - {metric}: {score}")

        print("\n" + "="*80)
        print("✅ All tests passed successfully!")
        print("="*80)
        print("\nDatabase Summary:")
        print(f"  Benchmark Runs:     {runs_count}")
        print(f"  Documents:          {docs_count}")
        print(f"  Questions:          {questions_count}")
        print(f"  Provider Results:   {provider_results_count}")
        print(f"  Question Results:   {question_results_count}")
        print()

    finally:
        await prisma.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
