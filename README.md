# RAGRace

A comprehensive platform for comparing and benchmarking different RAG (Retrieval-Augmented Generation) APIs and services.

## Overview

RAGRace provides a structured framework to evaluate and compare multiple RAG providers (e.g., LlamaIndex, LandingAI, etc.) using standardized datasets and scoring mechanisms. The platform automatically reads API documentation, creates unified interfaces, and evaluates performance using LLM-based scoring.

## Key Features

- **Multi-Provider Support**: Easy configuration-based system to add and compare different RAG APIs
- **Automated API Discovery**: Uses Playwright MCP to read API documentation and understand provider interfaces
- **Standardized Interface**: Normalizes input/output across different RAG providers for fair comparison
- **Dataset Flexibility**: Support for multiple datasets (SQuAD 2.0, domain-specific datasets) with custom preprocessing
- **LLM-Based Scoring**: Automated evaluation comparing RAG predictions against ground truth
- **Extensible Architecture**: Clean plugin-style design for adding new providers and datasets

## Workflow

```
1. Configure RAG Providers → 2. Read API Docs (Playwright) → 3. Generate Adapters
                                                                        ↓
7. Compare Results ← 6. Aggregate Scores ← 5. LLM Scoring ← 4. Query RAG APIs
                                                                        ↑
                                                              Dataset + Preprocessing
```

## Project Structure

```
RAGRace/
├── .claude.md                    # Claude Code project guidelines
├── README.md                     # This file
├── ARCHITECTURE.md               # Detailed architecture documentation
├── config/
│   ├── providers.yaml           # RAG provider configurations
│   ├── datasets.yaml            # Dataset configurations
│   └── scoring.yaml             # Scoring configurations
├── src/
│   ├── core/
│   │   ├── orchestrator.py      # Main workflow orchestrator
│   │   ├── adapter_factory.py   # Creates adapters for RAG providers
│   │   └── scorer.py            # LLM-based scoring engine
│   ├── adapters/
│   │   ├── base.py              # Base adapter interface
│   │   ├── llamaindex.py        # LlamaIndex adapter
│   │   ├── landingai.py         # LandingAI adapter
│   │   └── ...                  # Other provider adapters
│   ├── datasets/
│   │   ├── base.py              # Base dataset interface
│   │   ├── loader.py            # Dataset loading utilities
│   │   └── preprocessors/
│   │       ├── squad.py         # SQuAD preprocessing
│   │       └── custom.py        # Custom domain preprocessing
│   ├── api_discovery/
│   │   ├── doc_reader.py        # Playwright-based doc reading
│   │   └── adapter_generator.py # Auto-generate adapter code
│   └── utils/
│       ├── logger.py            # Logging utilities
│       └── metrics.py           # Performance metrics
├── data/
│   ├── datasets/                # Raw datasets
│   ├── cache/                   # Cached API responses
│   └── results/                 # Evaluation results
├── tests/
│   ├── unit/
│   └── integration/
├── notebooks/
│   └── analysis.ipynb           # Result analysis
└── requirements.txt             # Python dependencies
```

## Quick Start

### 1. Configure RAG Providers

Edit `config/providers.yaml`:

```yaml
providers:
  - name: llamaindex
    api_doc_url: https://docs.llamaindex.ai/...
    enabled: true

  - name: landingai
    api_doc_url: https://landing.ai/docs/...
    enabled: true
```

### 2. Run the Comparison

```bash
python -m src.core.orchestrator --dataset squad_v2 --providers all
```

### 3. View Results

```bash
python -m src.utils.report --results data/results/latest
```

## Configuration

### Provider Configuration

Each RAG provider requires:
- `name`: Unique identifier
- `api_doc_url`: URL to API documentation
- `api_key_env`: Environment variable for API key
- `enabled`: Whether to include in comparison

### Dataset Configuration

Datasets can be configured with:
- `name`: Dataset identifier
- `source`: Path or URL to dataset
- `format`: Dataset format (json, csv, etc.)
- `preprocessor`: Preprocessing module to use

### Scoring Configuration

LLM scoring can be customized:
- `model`: LLM model for evaluation
- `criteria`: Evaluation criteria
- `score_range`: Min/max score values

## Development

### Adding a New RAG Provider

1. Add provider config to `config/providers.yaml`
2. Run API discovery: `python -m src.api_discovery.doc_reader --provider <name>`
3. Review generated adapter in `src/adapters/<name>.py`
4. Test: `python -m pytest tests/unit/adapters/test_<name>.py`

### Adding a New Dataset

1. Add dataset config to `config/datasets.yaml`
2. Create preprocessor in `src/datasets/preprocessors/<name>.py`
3. Test: `python -m pytest tests/unit/datasets/test_<name>.py`

## Architecture Principles

- **Modularity**: Each component is independent and replaceable
- **Configuration-Driven**: Minimal code changes to add providers/datasets
- **Automated Discovery**: Reduce manual integration work
- **Fair Comparison**: Standardized interfaces ensure apples-to-apples comparison
- **Reproducibility**: All results are cached and versioned

## Contributing

