# RAGRace

**Benchmark and compare RAG providers on real-world datasets with one command.**

RAGRace provides an automated benchmark framework to evaluate RAG providers on academic documents, Wikipedia articles, and more. All providers are tested on identical documents with standardized evaluation metrics (Ragas) for fair comparison.

**Current Status**:
- **RAG Benchmarking**: Full orchestrator pipeline with 3 RAG providers, benchmarking on Qasper, PolicyQA, and SQuAD 2.0 datasets
- **PDF Parsing**: Interactive web UI to compare PDF parsing across LlamaIndex, Reducto, and LandingAI with cost estimation
- **Web Interface**: FastAPI + Prisma ORM + Next.js frontend with results visualization
- **Database**: Supabase PostgreSQL for persistent storage

## Integrated Providers

| Provider | Type | Key Features | Status |
|----------|------|--------------|--------|
| **[LlamaIndex](docs/ADAPTERS.md#llamaindex)** | Full RAG Framework | VectorStoreIndex, built-in embeddings | ✅ Tested |
| **[LandingAI](docs/ADAPTERS.md#landingai-ade-agentic-document-extraction)** | Doc Preprocessing | 8 chunk types, grounding metadata | ✅ Tested |
| **[Reducto](docs/ADAPTERS.md#reducto)** | Doc Preprocessing | Embedding-optimized, AI enrichment | ✅ Tested |

## PDF Parsing & Comparison

RAGRace includes an interactive web interface to compare PDF parsing quality across providers:

```bash
# Start backend API
cd backend
uvicorn main:app --reload

# Start frontend (in another terminal)
cd frontend
npm run dev

# Open browser
open http://localhost:3000/parse
```

**Features:**
- 📄 Upload PDFs and get instant page count analysis
- 💰 **Cost estimation** before parsing (configurable provider options)
- ⚙️ Provider configuration:
  - **LlamaIndex**: Choose parse mode (LLM vs Agent) and model (GPT-4o-mini, Sonnet 4.0)
  - **Reducto**: Toggle VLM enhancement (standard 1 credit/page vs complex 2 credits/page)
  - **LandingAI**: DPT-2 model
- 🔄 Side-by-side comparison with page navigation
- 📊 Processing time and actual cost tracking
- 💾 Download parsed results

**Workflow:** Upload PDF → Get page count → Review cost estimate → Configure providers → Parse & compare → Download results

## Web API

RAGRace provides a FastAPI-based REST API:

```bash
# Start the API server
cd backend
uvicorn main:app --reload

# API documentation
open http://localhost:8000/docs
```

**Benchmark Endpoints:**
- `GET /api/v1/results` - List all benchmark runs (paginated, filterable)
- `GET /api/v1/results/{run_id}` - Get full run details
- `GET /api/v1/datasets` - List available datasets

**Parsing Endpoints:**
- `POST /api/v1/parsing/upload` - Upload PDF file
- `POST /api/v1/parsing/page-count` - Get page count
- `POST /api/v1/parsing/compare` - Compare parsing across providers
- `GET /api/v1/parsing/download-result/{file_id}` - Download results

## Web Frontend

RAGRace includes a Next.js web interface:

```bash
cd frontend
npm install
npm run dev
open http://localhost:3000
```

**Pages:**
- 📊 **Home** (`/`) - Browse all benchmark runs with sortable table
- 🔍 **Run Details** (`/results/[id]`) - Detailed provider comparison with charts
- 📚 **Datasets** (`/datasets`) - Available datasets info
- 📄 **Parse** (`/parse`) - Interactive PDF parsing comparison with cost estimation

**Features:**
- Expandable question-by-question results
- Ground truth vs provider answers
- Evaluation scores and latency metrics
- Responsive design with shadcn/ui
- Interactive charts and visualizations

See [frontend/README.md](frontend/README.md) for complete documentation.

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/yourusername/RAGRace.git
cd RAGRace

# Install backend dependencies
cd backend
pip install -r requirements.txt
```

### 2. API Keys Setup

```bash
# Copy environment template (in backend/)
cp backend/.env.example backend/.env

# Edit backend/.env and add your API keys:
# OPENAI_API_KEY=sk-...                    # Required for all providers
# VISION_AGENT_API_KEY=va-...              # For LandingAI (optional)
# REDUCTO_API_KEY=red-...                   # For Reducto (optional)
# DATABASE_URL=postgresql://...             # Supabase connection (for API)
```

**Note**: You only need OpenAI API key to run LlamaIndex. Add other keys only if testing those providers.

### 3. Run Your First Benchmark

```bash
# Quick test: 1 document, 1 question per document (~2 minutes, ~$0.10)
python backend/scripts/run_benchmark.py --docs 1 --questions 1

# Small benchmark: 2 documents, 3 questions each (~5 minutes, ~$1.00)
python backend/scripts/run_benchmark.py --docs 2 --questions 3

# Test specific providers only
python backend/scripts/run_benchmark.py --docs 1 --questions 1 --providers llamaindex
```

**What happens when you run this?**
1. Downloads Qasper dataset from HuggingFace (first run only)
2. Downloads research document PDFs from arxiv (cached locally)
3. Executes all (provider, document) combinations in parallel with rate limiting
4. Evaluates with Ragas metrics (faithfulness, factual correctness, context recall)
5. Saves results incrementally to `data/results/run_YYYYMMDD_HHMMSS/`

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
    max_docs: 10                       # Limit documents (null = all)
    max_questions_per_doc: 5           # Questions per document (null = all)

  providers:                           # Add/remove providers
    - llamaindex
    - reducto

  execution:
    # NEW: Parallel task execution (provider × document combinations)
    max_total_workers: 9               # Total parallel tasks (e.g., 3 docs × 3 providers)
    max_per_provider_workers: 3        # Max concurrent tasks per provider (rate limiting)
    max_ragas_workers: 5               # Max concurrent RAGAS evaluations (OpenAI protection)
```

**Parallelization Model**:
- Tasks are (provider, document) combinations executed in parallel
- `max_total_workers`: Controls overall system concurrency
- `max_per_provider_workers`: Prevents overwhelming individual provider APIs
- `max_ragas_workers`: Protects OpenAI evaluation API from rate limits

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
- 1 document, 1 question: ~$0.10 (quick test)
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
├── backend/                  # Python backend (benchmarking + parsing + API)
│   ├── main.py               # FastAPI app entry point
│   ├── api/                  # REST API (benchmarks + parsing endpoints)
│   │   ├── models/           # Pydantic models
│   │   └── routers/          # Endpoint handlers (results, parsing)
│   ├── prisma/               # Prisma ORM (Supabase PostgreSQL)
│   ├── scripts/
│   │   └── run_benchmark.py  # CLI for running benchmarks
│   ├── config/
│   │   ├── benchmark_*.yaml      # Benchmark configs
│   │   ├── providers.yaml        # Provider registry
│   │   └── parsing_pricing.yaml  # Parsing cost config
│   ├── src/
│   │   ├── core/             # Orchestrator, executor, evaluator
│   │   ├── adapters/         # RAG + parsing adapters
│   │   │   ├── llamaindex_adapter.py, landingai_adapter.py, reducto_adapter.py
│   │   │   └── parsing/      # Parsing adapters (3 providers)
│   │   └── datasets/         # Dataset loaders
│   └── tests/                # 55+ unit + integration tests
├── frontend/                 # Next.js 16 (TypeScript, Tailwind, shadcn/ui)
│   ├── app/                  # Pages (/, /results/[id], /datasets, /parse)
│   ├── components/           # React components
│   │   ├── parse/            # Parsing UI (upload, cost, comparison)
│   │   ├── results/          # Benchmark results UI
│   │   └── ui/               # shadcn/ui components
│   ├── lib/                  # API client, utilities
│   └── types/                # TypeScript types
├── data/                     # Datasets + results (auto-cached)
│   ├── datasets/             # Qasper, PolicyQA, SQuAD2
│   └── results/              # Benchmark results (timestamped)
├── docs/                     # Documentation
│   ├── ARCHITECTURE.md       # System architecture
│   ├── ADAPTERS.md           # Adapter specifications
│   └── DEVELOPMENT.md        # Development guide
└── local_docs/               # AI working docs
```

## Documentation

- **[Architecture](docs/ARCHITECTURE.md)** - System design and components
- **[Adapter Reference](docs/ADAPTERS.md)** - Detailed adapter specs and comparison
- **[Development Guide](docs/DEVELOPMENT.md)** - How to add new providers
- **[Project Plan](local_docs/PROJECT_PLAN.md)** - Development roadmap (AI continuity)

## Key Features

### 🎯 RAG Benchmarking

- **Ragas Metrics**: Faithfulness, Factual Correctness, Context Recall
- **Fair Comparison**: All providers tested on identical PDFs with identical questions
- **Standardized Interface**: All providers implement `BaseAdapter`
- **Real Documents**: Full-length research documents (10K+ tokens), not toy examples
- **3 RAG Providers**: LlamaIndex, LandingAI, Reducto
- **3 Datasets**: Qasper (research papers), PolicyQA (privacy policies), SQuAD 2.0 (Wikipedia)
- **Parallel Execution**: Semaphore-based rate limiting for (provider, document) tasks

### 📄 PDF Parsing Comparison

- **3 Parsing Providers**: LlamaIndex, Reducto, LandingAI
- **Cost Estimation**: Preview costs before parsing with configurable provider options
- **Quality Comparison**: Side-by-side markdown output with page navigation
- **Flexible Configuration**: Choose parse modes, models, and enhancement options per provider
- **Transparent Pricing**: Real-time cost tracking with detailed breakdowns
- **Interactive UI**: Upload, configure, compare, and download results

### 🔧 Technical

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
