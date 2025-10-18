# RAGRace

**Benchmark and compare RAG providers on real-world datasets with one command.**

RAGRace provides an automated benchmark framework to evaluate RAG providers on academic documents, Wikipedia articles, and more. All providers are tested on identical documents with standardized evaluation metrics (Ragas) for fair comparison.

**Current Status**: Checkpoint 5 Complete - Full orchestrator pipeline with 3 RAG providers, automated benchmarking on Qasper (research papers), PolicyQA (privacy policies), and SQuAD 2.0 datasets.

## Integrated Providers

| Provider | Type | Key Features | Status |
|----------|------|--------------|--------|
| **[LlamaIndex](docs/ADAPTERS.md#llamaindex)** | Full RAG Framework | VectorStoreIndex, built-in embeddings | ✅ Tested |
| **[LandingAI](docs/ADAPTERS.md#landingai-ade-agentic-document-extraction)** | Doc Preprocessing | 8 chunk types, grounding metadata | ✅ Tested |
| **[Reducto](docs/ADAPTERS.md#reducto)** | Doc Preprocessing | Embedding-optimized, AI enrichment | ✅ Tested |

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/yourusername/RAGRace.git
cd RAGRace

# Install dependencies
pip install -r requirements.txt
```

### 2. API Keys Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys:
# OPENAI_API_KEY=sk-...                    # Required for all providers
# VISION_AGENT_API_KEY=va-...              # For LandingAI (optional)
# REDUCTO_API_KEY=red-...                   # For Reducto (optional)
```

**Note**: You only need OpenAI API key to run LlamaIndex. Add other keys only if testing those providers.

### 3. Run Your First Benchmark

```bash
# Quick test: 1 document, 1 question per document (~2 minutes, ~$0.20)
python scripts/run_benchmark.py --docs 1 --questions 1

# Small benchmark: 2 documents, 3 questions each (~5 minutes, ~$1.00)
python scripts/run_benchmark.py --docs 2 --questions 3

# Test specific providers only
python scripts/run_benchmark.py --docs 1 --questions 1 --providers llamaindex
```

**What happens when you run this?**
1. Downloads Qasper dataset from HuggingFace (first run only)
2. Downloads research document PDFs from arxiv (cached locally)
3. Runs 3 RAG providers in parallel on the same documents
4. Evaluates with Ragas metrics (faithfulness, factual correctness, context recall)
5. Saves structured results to `data/results/run_YYYYMMDD_HHMMSS/`

### 4. View Results

```bash
# Results are saved in structured JSON format
cat data/results/run_*/summary.json

# Each document has detailed provider results
cat data/results/run_*/docs/1909.00694/llamaindex_results.json
```

**Result Structure**:
```
data/results/run_20251018_103045/
├── docs/
│   ├── 1909.00694/                    # Per-document results
│   │   ├── llamaindex_results.json    # LlamaIndex results + Ragas scores
│   │   ├── landingai_results.json     # LandingAI results + Ragas scores
│   │   └── reducto_results.json       # Reducto results + Ragas scores
│   └── ...
├── summary.json                        # Aggregated metrics across all documents
└── benchmark_config.yaml               # Config snapshot for reproducibility
```

## Datasets

RAGRace supports multiple datasets for evaluation:

| Dataset | Type | Documents | Questions | Download | Status |
|---------|------|-----------|-----------|----------|--------|
| **Qasper** | Research Papers (NLP) | 1,585 | 5,049 | Auto from arxiv | ✅ Supported |
| **PolicyQA** | Privacy Policies | 115 | 25,017 | Auto (HTML→PDF) | ✅ Supported |
| **SQuAD 2.0** | Wikipedia Articles | - | 150K+ | Auto from HuggingFace | ✅ Supported |

### Dataset Download (Automatic)

**No manual download needed!** Datasets are automatically downloaded on first run:

1. **Qasper**:
   - Metadata downloaded from HuggingFace (`.parquet` files)
   - PDFs downloaded from arxiv on-demand (cached in `data/datasets/Qasper/pdfs/`)
   - Rate-limited to respect arxiv (3s between downloads)

2. **PolicyQA**:
   - JSON Q&A data downloaded from GitHub
   - HTML policy documents converted to PDF via Playwright (cached in `data/datasets/PolicyQA/pdfs/`)
   - Preserves full document structure (layout, tables, formatting)

3. **SQuAD 2.0**:
   - JSON files downloaded from HuggingFace if needed
   - Cached in `data/datasets/SQuAD2/`

**Storage locations:**
```
data/datasets/
├── Qasper/
│   ├── dataset.yaml          # Metadata (committed to git)
│   ├── cache/*.parquet       # HuggingFace dataset cache (NOT in git)
│   └── pdfs/*.pdf            # Downloaded PDFs (NOT in git)
├── PolicyQA/
│   ├── dataset.yaml          # Metadata (committed to git)
│   ├── *.json                # Q&A data from GitHub (NOT in git)
│   ├── original_policies/    # HTML files (NOT in git)
│   └── pdfs/*.pdf            # Generated PDFs (NOT in git)
└── SQuAD2/
    ├── dataset.yaml          # Metadata (committed to git)
    └── *.json                # Dataset files (NOT in git)
```

**Cache behavior:**
- First run: Downloads datasets and PDFs (~5-10 minutes for 10 documents)
- Subsequent runs: Uses cached files (instant)
- Failed downloads: Automatically skipped (benchmark continues)

### Qasper Dataset Details

**Why Qasper?**
- **Real research documents**: Full-length NLP documents from arxiv (10K+ tokens)
- **Expert annotations**: Questions by readers, answers by NLP practitioners
- **Diverse questions**: Extractive, abstractive, boolean, unanswerable
- **Evidence grounding**: Answers linked to document sections
- **Realistic challenge**: Tests RAG on long-form scientific documents

**Dataset splits:**
- Train: 888 documents, ~2,850 questions
- Validation: 281 documents, ~900 questions
- Test: 416 documents, ~1,300 questions

## Advanced Usage

### Benchmark Configuration

Pre-configured benchmark files:
- `config/benchmark_qasper.yaml` - Qasper (research papers)
- `config/benchmark_policyqa.yaml` - PolicyQA (privacy policies)

Example configuration:

```yaml
benchmark:
  dataset:
    name: qasper                       # qasper | policyqa | squad2
    split: train                       # train | validation | test (Qasper)
                                       # train | dev | test (PolicyQA)
    max_docs: 2                        # Limit documents (null = all)
    max_questions_per_doc: 3           # Questions per document (null = all)

  providers:                           # Add/remove providers
    - llamaindex
    - landingai
    - reducto

  execution:
    max_provider_workers: 3            # Parallel providers per document
    max_doc_workers: 1                 # Parallel documents (sequential by default)
```

### CLI Options

```bash
# Use specific config file
python scripts/run_benchmark.py --config config/benchmark_qasper.yaml
python scripts/run_benchmark.py --config config/benchmark_policyqa.yaml

# Override config file settings
python scripts/run_benchmark.py --config config/benchmark_qasper.yaml --docs 10 --questions 5

# Test specific providers
python scripts/run_benchmark.py --providers llamaindex reducto

# Resume interrupted benchmark
python scripts/run_benchmark.py --resume run_20251018_103045
```

### Cost Estimation

**Per document (3 providers, 3 questions):**
- Document parsing: ~$0.10 (PDF → chunks)
- Query processing: ~$0.15 (3 questions × 3 providers)
- Ragas evaluation: ~$0.25 (3 questions × 3 metrics × 3 providers)
- **Total: ~$0.50 per document**

**Common benchmarks:**
- 1 document, 1 question: ~$0.20 (quick test)
- 10 documents, 3 questions: ~$5.00 (small benchmark)
- 100 documents, all questions: ~$50+ (full evaluation)

### Development Testing

For development, use pytest to run unit tests (no API costs):

```bash
# Run all unit tests (fast, no API calls)
pytest tests/ -v -k "not integration"

# Run integration tests (real API calls, costs money)
pytest tests/ -v -m integration -s
```

## Project Structure

```
RAGRace/
├── scripts/
│   └── run_benchmark.py      # ⭐ CLI entry point for benchmarks
├── config/
│   ├── benchmark_qasper.yaml      # Qasper benchmark config
│   ├── benchmark_policyqa.yaml    # PolicyQA benchmark config
│   ├── providers.yaml             # Provider registry (human-maintained)
│   └── providers.generated.yaml   # Provider configs (AI-generated)
├── src/
│   ├── core/                 # Core pipeline components
│   │   ├── orchestrator.py   # Main benchmark coordinator
│   │   ├── adapter_factory.py    # Provider instantiation
│   │   ├── provider_executor.py  # Parallel execution
│   │   ├── document_processor.py # Document processing
│   │   ├── result_saver.py       # Results management
│   │   ├── ragas_evaluator.py    # Ragas metrics
│   │   └── schemas.py            # Data structures
│   ├── adapters/             # RAG provider adapters
│   │   ├── base.py           # BaseAdapter interface
│   │   ├── llamaindex_adapter.py
│   │   ├── landingai_adapter.py
│   │   └── reducto_adapter.py
│   └── datasets/             # Dataset loaders
│       ├── loader.py         # Main loader
│       └── preprocessors/    # Dataset-specific preprocessing
├── tests/                    # Unit and integration tests
├── data/
│   ├── datasets/             # Downloaded datasets (auto-cached)
│   │   ├── Qasper/           # Research papers (arxiv PDFs)
│   │   ├── PolicyQA/         # Privacy policies (HTML→PDF)
│   │   └── SQuAD2/           # Wikipedia articles
│   └── results/              # Benchmark results (timestamped)
└── docs/                     # Documentation
    ├── ARCHITECTURE.md       # System architecture
    ├── ADAPTERS.md           # Adapter specifications
    └── DEVELOPMENT.md        # Development guide
```

## Documentation

- **[Architecture](docs/ARCHITECTURE.md)** - System design and components
- **[Adapter Reference](docs/ADAPTERS.md)** - Detailed adapter specs and comparison
- **[Development Guide](docs/DEVELOPMENT.md)** - How to add new providers
- **[Project Plan](local_docs/PROJECT_PLAN.md)** - Development roadmap (AI continuity)

## Key Features

### 🎯 Evaluation & Fairness

- **Ragas Metrics**: Faithfulness, Factual Correctness, Context Recall
- **Fair Comparison**: All providers tested on identical PDFs with identical questions
- **Standardized Interface**: All providers implement `BaseAdapter`
- **Real Documents**: Full-length research documents (10K+ tokens), not toy examples

### 🔧 Technical

- **3 RAG Providers**: LlamaIndex, LandingAI, Reducto
- **3 Datasets**: Qasper (research papers), PolicyQA (privacy policies), SQuAD 2.0 (Wikipedia)
- **HTML→PDF Pipeline**: Playwright-based conversion preserving document structure
- **54+ Tests**: Unit and integration tests with real API validation
- **Web Research**: Uses Playwright MCP to read actual API documentation (NO IMAGINATION)

## Development

Want to add a new RAG provider? Follow the **NO IMAGINATION** rule:

1. Research actual API docs with web-research-gatherer subagent
2. Implement adapter based on real documentation
3. Write unit + integration tests
4. Update documentation

See **[Development Guide](docs/DEVELOPMENT.md)** for detailed instructions.

## Contributing

Contributions welcome! Please:
- Follow the existing adapter patterns
- Base implementations on actual API documentation
- Include both unit and integration tests
- Update documentation

## License

MIT License

## Contact

For questions or issues, please open a GitHub issue.
