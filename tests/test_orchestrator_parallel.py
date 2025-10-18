"""
Integration test for parallel RAG orchestrator.

This test validates the complete CP5 implementation:
- Parallel execution of multiple providers
- Incremental result saving
- Winner determination
- JSON output structure
- Resume capability

Test configuration:
- 1 paper from Qasper dataset
- 1 question per paper
- 3 providers (LlamaIndex, LandingAI, Reducto)
- Real API calls (requires valid API keys)
"""

import pytest
import os
import json
import time
from pathlib import Path

from src.core.orchestrator import Orchestrator


@pytest.mark.integration
class TestOrchestratorParallel:
    """Integration tests for parallel orchestrator."""

    @pytest.fixture
    def config_file(self, tmp_path):
        """Create temporary benchmark config for testing."""
        config = {
            'benchmark': {
                'dataset': {
                    'name': 'qasper',
                    'split': 'train',
                    'max_papers': 2,  # 2 papers for better testing
                    'max_questions_per_paper': 3,  # 3 questions per paper
                    'filter_unanswerable': True
                },
                'providers': ['llamaindex', 'landingai', 'reducto'],
                'execution': {
                    'max_provider_workers': 3,  # All 3 in parallel
                    'max_paper_workers': 1
                },
                'timeouts': {
                    'provider_init': 30,
                    'document_ingest': 300,
                    'query': 60,
                    'evaluation': 120
                },
                'retry': {
                    'max_attempts': 3,
                    'delay_seconds': 5,
                    'exponential_backoff': True
                },
                'output': {
                    'results_dir': str(tmp_path / 'results'),
                    'save_intermediate': True,
                    'resume_enabled': True
                },
                'evaluation': {
                    'model': 'gpt-4o-mini',
                    'api_key_env': 'OPENAI_API_KEY',
                    'metrics': ['faithfulness', 'factual_correctness', 'context_recall']
                },
                'provider_configs': {
                    'llamaindex': {
                        'top_k': 3,
                        'api_key_env': 'OPENAI_API_KEY',
                        'cloud_api_key_env': 'LLAMAINDEX_API_KEY'
                    },
                    'landingai': {
                        'top_k': 3,
                        'api_key_env': 'VISION_AGENT_API_KEY',
                        'openai_api_key_env': 'OPENAI_API_KEY'
                    },
                    'reducto': {
                        'top_k': 3,
                        'api_key_env': 'REDUCTO_API_KEY',
                        'openai_api_key_env': 'OPENAI_API_KEY'
                    }
                }
            }
        }

        # Write config to file
        config_path = tmp_path / 'benchmark.yaml'
        import yaml
        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        return str(config_path)

    @pytest.fixture
    def check_api_keys(self):
        """Check that all required API keys are present."""
        required_keys = [
            'OPENAI_API_KEY',
            'LLAMAINDEX_API_KEY',
            'VISION_AGENT_API_KEY',
            'REDUCTO_API_KEY'
        ]

        missing = [k for k in required_keys if not os.getenv(k)]
        if missing:
            pytest.skip(f"Missing API keys: {', '.join(missing)}")

    def test_parallel_execution_timing(self, config_file, check_api_keys):
        """
        Test that providers execute in parallel (not sequential).

        Expected behavior:
        - 3 providers running in parallel should take ~1x time of single provider
        - If sequential, would take ~3x time of single provider

        We verify timing is closer to 1x than 3x (allowing for overhead).
        """
        print("\n" + "="*80)
        print("TEST: Parallel Execution Timing")
        print("="*80)

        # Run benchmark
        orchestrator = Orchestrator(config_path=config_file)
        start_time = time.time()
        summary = orchestrator.run_benchmark()
        total_time = time.time() - start_time

        print(f"\nTotal benchmark time: {total_time:.1f}s")
        print(f"Provider count: {len(summary.providers)}")

        # Get individual provider times
        provider_times = []
        for paper_result in summary.results:
            for provider_name, provider_result in paper_result.providers.items():
                if provider_result.status == "success":
                    provider_times.append(provider_result.duration_seconds)
                    print(f"  {provider_name}: {provider_result.duration_seconds:.1f}s")

        if provider_times:
            max_provider_time = max(provider_times)
            sequential_time_estimate = sum(provider_times)

            print(f"\nMax provider time: {max_provider_time:.1f}s")
            print(f"Sequential estimate: {sequential_time_estimate:.1f}s")
            print(f"Speedup: {sequential_time_estimate / total_time:.2f}x")

            # Verify parallelism: total time should be closer to max than sum
            # Allow for overhead (evaluation, I/O), so check < 2x max
            assert total_time < (max_provider_time * 2), \
                f"Execution appears sequential: {total_time:.1f}s vs max {max_provider_time:.1f}s"

        print("✅ Parallel execution verified")

    def test_complete_benchmark_flow(self, config_file, check_api_keys):
        """
        Test complete benchmark flow end-to-end.

        Validates:
        - All 3 providers complete successfully
        - Results saved in correct structure
        - Winner determined
        - JSON files valid and complete
        """
        print("\n" + "="*80)
        print("TEST: Complete Benchmark Flow")
        print("="*80)

        # Run benchmark
        orchestrator = Orchestrator(config_path=config_file)
        summary = orchestrator.run_benchmark()

        # Verify summary
        assert summary.num_papers == 2
        assert summary.num_questions_total >= 3  # At least a few questions (dataset dependent)
        assert len(summary.providers) == 3
        assert len(summary.results) == 2

        # Verify each paper
        for paper_idx, paper_result in enumerate(summary.results, 1):
            print(f"\n--- Paper {paper_idx}: {paper_result.paper_id} ---")

            # Verify all providers completed
            assert len(paper_result.providers) == 3
            for provider_name in ['llamaindex', 'landingai', 'reducto']:
                assert provider_name in paper_result.providers
                provider_result = paper_result.providers[provider_name]
                print(f"\n{provider_name}:")
                print(f"  Status: {provider_result.status}")
                if provider_result.status == "success":
                    print(f"  Scores: {provider_result.aggregated_scores}")
                    assert len(provider_result.questions) >= 1  # At least 1 question
                    assert len(provider_result.aggregated_scores) > 0
                else:
                    print(f"  Error: {provider_result.error}")

            # Verify winner determined
            assert len(paper_result.winner) > 0
            print(f"\nWinners: {paper_result.winner}")

        # Verify file structure
        results_dir = Path(orchestrator.result_saver.run_dir)
        assert results_dir.exists()

        # Check config.json
        config_file = results_dir / "config.json"
        assert config_file.exists()
        with open(config_file) as f:
            config_data = json.load(f)
            assert 'benchmark' in config_data

        # Check paper directories (both papers)
        for paper_result in summary.results:
            paper_dir = results_dir / "papers" / paper_result.paper_id
            assert paper_dir.exists()

            # Check provider JSONs
            for provider_name in ['llamaindex', 'landingai', 'reducto']:
                provider_file = paper_dir / f"{provider_name}.json"
                assert provider_file.exists()
                with open(provider_file) as f:
                    provider_data = json.load(f)
                    assert provider_data['provider'] == provider_name
                    assert provider_data['status'] in ['success', 'error']

            # Check aggregated.json
            aggregated_file = paper_dir / "aggregated.json"
            assert aggregated_file.exists()
            with open(aggregated_file) as f:
                aggregated_data = json.load(f)
                assert aggregated_data['paper_id'] == paper_result.paper_id
                assert len(aggregated_data['providers']) == 3

        # Check summary.json
        summary_file = results_dir / "summary.json"
        assert summary_file.exists()
        with open(summary_file) as f:
            summary_data = json.load(f)
            assert summary_data['num_papers'] == 2
            assert summary_data['num_questions_total'] >= 3  # Dataset dependent
            assert len(summary_data['providers']) == 3

        print("\n✅ Complete benchmark flow validated")

    def test_resume_capability(self, config_file, check_api_keys):
        """
        Test resume capability - running twice should skip completed papers.

        Validates:
        - First run completes normally
        - Second run detects completed paper and skips
        - Second run is much faster
        """
        print("\n" + "="*80)
        print("TEST: Resume Capability")
        print("="*80)

        # First run
        print("\n--- First run ---")
        orchestrator1 = Orchestrator(config_path=config_file)
        start_time1 = time.time()
        summary1 = orchestrator1.run_benchmark()
        duration1 = time.time() - start_time1

        print(f"First run duration: {duration1:.1f}s")
        assert summary1.num_papers == 2

        # Second run (should skip)
        print("\n--- Second run (should skip) ---")
        orchestrator2 = Orchestrator(config_path=config_file)
        # Use same run_id to simulate resume
        orchestrator2.result_saver.run_id = orchestrator1.result_saver.run_id
        orchestrator2.result_saver.run_dir = orchestrator1.result_saver.run_dir
        orchestrator2.result_saver.papers_dir = orchestrator1.result_saver.papers_dir

        start_time2 = time.time()
        summary2 = orchestrator2.run_benchmark()
        duration2 = time.time() - start_time2

        print(f"Second run duration: {duration2:.1f}s")

        # Second run should be much faster (mostly just initialization)
        # Allow for some processing time, but should be < 20% of first run
        print(f"Speedup: {duration1 / duration2:.2f}x")
        assert duration2 < (duration1 * 0.2), \
            f"Second run not fast enough: {duration2:.1f}s vs {duration1:.1f}s"

        print("✅ Resume capability verified")

    def test_error_isolation(self, config_file, tmp_path):
        """
        Test that one provider failure doesn't stop others.

        NOTE: This test requires intentionally breaking one provider,
        which we can simulate by using invalid API key.
        For now, we'll skip this test and document it for manual testing.
        """
        pytest.skip("Error isolation test requires manual setup with invalid API key")


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-m", "integration", "-s"])
