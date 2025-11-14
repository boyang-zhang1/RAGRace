#!/usr/bin/env python3
"""
DocAgent-Arena Benchmark Runner - CLI Script

Run RAG provider benchmarks from the command line.

Usage:
    # Run with default config
    python scripts/run_benchmark.py

    # Run with custom config
    python scripts/run_benchmark.py --config config/my_benchmark.yaml

    # Override dataset parameters
    python scripts/run_benchmark.py --docs 5 --questions 10

    # Run specific providers only
    python scripts/run_benchmark.py --providers llamaindex reducto

    # Resume interrupted run
    python scripts/run_benchmark.py --resume run_20251018_103045

Examples:
    # Quick test: 1 doc, 1 question
    python scripts/run_benchmark.py --docs 1 --questions 1

    # Small benchmark: 2 docs, 3 questions
    python scripts/run_benchmark.py --docs 2 --questions 3

    # Full benchmark: all docs, all questions
    python scripts/run_benchmark.py --docs null --questions null
"""

import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent  # backend/scripts -> backend
sys.path.insert(0, str(project_root))

# Load environment variables from backend/.env file
env_file = project_root / '.env'
if env_file.exists():
    load_dotenv(env_file)
else:
    print("⚠️  No .env file found in backend/ (using system environment variables)")

from src.core.orchestrator import Orchestrator


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run DocAgent-Arena benchmark to compare RAG providers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Config file
    parser.add_argument(
        '--config',
        type=str,
        default='config/benchmark_qasper.yaml',
        help='Path to benchmark configuration file (default: config/benchmark_qasper.yaml)'
    )

    # Dataset overrides
    parser.add_argument(
        '--dataset',
        type=str,
        help='Dataset name (overrides config)'
    )

    parser.add_argument(
        '--docs',
        type=str,
        help='Max docs to process (number or "null" for all, overrides config)'
    )

    parser.add_argument(
        '--questions',
        type=str,
        help='Max questions per doc (number or "null" for all, overrides config)'
    )

    # Provider selection
    parser.add_argument(
        '--providers',
        type=str,
        nargs='+',
        help='Providers to test (overrides config, e.g., --providers llamaindex reducto)'
    )

    # Execution options
    parser.add_argument(
        '--workers',
        type=int,
        help='Max concurrent provider workers (overrides config)'
    )

    # Resume capability
    parser.add_argument(
        '--resume',
        type=str,
        help='Resume from run ID (e.g., run_20251018_103045)'
    )

    # Output options
    parser.add_argument(
        '--output-dir',
        type=str,
        help='Results output directory (overrides config)'
    )

    parser.add_argument(
        '--no-resume',
        action='store_true',
        help='Disable resume capability (reprocess all documents)'
    )

    # Verbose output
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    return parser.parse_args()


def override_config(config: dict, args: argparse.Namespace) -> dict:
    """
    Override configuration with command-line arguments.

    Args:
        config: Original config dict
        args: Parsed command-line arguments

    Returns:
        Modified config dict
    """
    benchmark_config = config['benchmark']

    # Dataset overrides
    if args.dataset:
        benchmark_config['dataset']['name'] = args.dataset

    if args.docs:
        if args.docs.lower() == 'null':
            benchmark_config['dataset']['max_docs'] = None
        else:
            benchmark_config['dataset']['max_docs'] = int(args.docs)

    if args.questions:
        if args.questions.lower() == 'null':
            benchmark_config['dataset']['max_questions_per_doc'] = None
        else:
            benchmark_config['dataset']['max_questions_per_doc'] = int(args.questions)

    # Provider overrides
    if args.providers:
        benchmark_config['providers'] = args.providers

    # Execution overrides
    if args.workers:
        benchmark_config['execution']['max_provider_workers'] = args.workers

    # Output overrides
    if args.output_dir:
        benchmark_config['output']['results_dir'] = args.output_dir

    if args.no_resume:
        benchmark_config['output']['resume_enabled'] = False

    return config


def main():
    """Main entry point."""
    args = parse_args()

    print("="*80)
    print("DocAgent-Arena Benchmark Runner")
    print("="*80)

    # Confirm .env loaded
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        print(f"✓ Loaded .env file")
    else:
        print(f"⚠️  No .env file found (using system environment variables)")

    # Check config file exists
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        print(f"   Please create a config file or use --config to specify path")
        sys.exit(1)

    print(f"Config: {config_path}")

    # Load and override config
    import yaml
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Apply command-line overrides
    if any([args.dataset, args.docs, args.questions, args.providers,
            args.workers, args.output_dir, args.no_resume]):
        print("\nApplying command-line overrides:")
        if args.dataset:
            print(f"  Dataset: {args.dataset}")
        if args.docs:
            print(f"  Max docs: {args.docs}")
        if args.questions:
            print(f"  Max questions: {args.questions}")
        if args.providers:
            print(f"  Providers: {', '.join(args.providers)}")
        if args.workers:
            print(f"  Workers: {args.workers}")
        if args.output_dir:
            print(f"  Output dir: {args.output_dir}")
        if args.no_resume:
            print(f"  Resume: disabled")

        config = override_config(config, args)

        # Save modified config to temp file
        temp_config_path = Path('.ragrace_temp_config.yaml')
        with open(temp_config_path, 'w') as f:
            yaml.dump(config, f)
        config_path = temp_config_path

    # Run benchmark
    try:
        orchestrator = Orchestrator(config_path=str(config_path))

        # Handle resume
        if args.resume:
            print(f"\n📂 Resuming from run: {args.resume}")
            orchestrator.result_saver.run_id = args.resume
            orchestrator.result_saver.run_dir = Path(config['benchmark']['output']['results_dir']) / args.resume
            orchestrator.result_saver.docs_dir = orchestrator.result_saver.run_dir / "docs"

        summary = orchestrator.run_benchmark()

        # Cleanup temp config if created
        if config_path.name == '.ragrace_temp_config.yaml':
            config_path.unlink()

        print(f"\n✅ Benchmark completed successfully!")
        print(f"   Results: {orchestrator.result_saver.run_dir}")

        return 0

    except KeyboardInterrupt:
        print(f"\n\n⚠️  Benchmark interrupted by user")
        print(f"   Partial results saved to: {orchestrator.result_saver.run_dir}")
        print(f"   Resume with: --resume {orchestrator.result_saver.run_id}")
        return 130

    except Exception as e:
        print(f"\n\n❌ Benchmark failed: {e}")
        import traceback
        if args.verbose:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
