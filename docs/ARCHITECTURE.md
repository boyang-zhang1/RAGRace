# RAGRace Architecture

## Components

### Core Pipeline (`src/core/`)
- **orchestrator.py** - Main benchmark coordinator
  - Loads configuration and datasets
  - Creates (provider, document) task combinations
  - Manages semaphore-based rate limiting (per-provider + RAGAS)
  - Executes tasks in parallel with ThreadPoolExecutor
  - Aggregates and saves final results
- **adapter_factory.py** - Dynamic provider instantiation
  - Creates adapter instances from config
  - Handles provider-specific initialization
  - Manages API key injection from environment
- **provider_executor.py** - Individual task execution with rate limiting
  - Executes one (provider, document) combination
  - Acquires/releases semaphores for rate limiting
  - Handles timeouts and errors gracefully
  - Tracks costs and performance per task
- **document_processor.py** - DEPRECATED (kept for backward compatibility)
  - Legacy: Coordinated provider execution per document
  - New code uses Orchestrator.run_benchmark() directly
- **result_saver.py** - Thread-safe results management
  - Saves structured JSON results with file locks
  - Enables resume from interruptions (task-level)
  - Creates timestamped run directories
  - Generates summary aggregations
- **schemas.py** - Data structures (CP5)
  - BenchmarkConfig, DocumentResult, ProviderResult
  - Standardized result format across providers
- **ragas_evaluator.py** - Ragas metric evaluation
  - Faithfulness, Factual Correctness, Context Recall
  - Batch evaluation for efficiency
- **scorer.py** - Batch LLM scoring (GPT structured outputs)
  - Legacy scorer for comparison
- **rag_logger.py** - Structured logging for multi-document experiments

### Adapters (`src/adapters/`)
- **base.py** - BaseAdapter interface (ALL providers must implement)
- **llamaindex_adapter.py** - LlamaIndex integration (VectorStoreIndex)
- **landingai_adapter.py** - LandingAI ADE integration (document preprocessing)
- **reducto_adapter.py** - Reducto integration (RAG-optimized processing)
- **__init__.py** - Exports all adapters

### Datasets (`src/datasets/`)
- **loader.py** - Load datasets
- **preprocessors/*.py** - Dataset-specific preprocessing

### API Discovery (Web Research Process)
- Uses **web-research-gatherer subagent** (Task tool with general-purpose type)
- Reads actual API documentation via Playwright MCP
- Creates research documents in `local_docs/research_*_api_*.md`
- No imagination - only actual API information
- Manual adapter implementation based on research docs

## Interfaces

### BaseAdapter
```python
class BaseAdapter(ABC):
    def initialize(api_key: str, **kwargs) -> None
    def ingest_documents(documents: List[Document]) -> str  # returns index_id
    def query(question: str, index_id: str, **kwargs) -> RAGResponse
    def health_check() -> bool
```

### Data Structures
```python
Document(id, content, metadata)
RAGResponse(answer, context, metadata, latency_ms, tokens_used)
```

## Scoring

**Batch mode**: All providers' predictions in ONE GPT call
- Fairness (LLM sees all together)
- Efficiency (save tokens)

**Metrics**:
- Exact Match (0/1) - SQuAD-style normalization
- Semantic Score (0-100) - GPT evaluation

**Model**: gpt-4o-mini with structured outputs

## Implemented Providers

### LlamaIndex
- **Type**: Full RAG framework
- **Components**: LlamaParse (PDF) + VectorStoreIndex + OpenAI embeddings + OpenAI LLM
- **Storage**: In-memory SimpleVectorStore
- **Features**: Cloud PDF parsing, automatic chunking, semantic retrieval, response synthesis
- **Requirements**: PDF files via `file_path` metadata
- **Tests**: 11 unit + 3 integration

### LandingAI ADE (Agentic Document Extraction)
- **Type**: Document preprocessing + RAG completion
- **Components**: ADE API + external embeddings + external LLM
- **Parsing**: 8 semantic chunk types (text, table, figure, logo, card, etc.)
- **Features**: Grounding metadata, bounding boxes, multi-modal
- **Requirements**: PDF files via `file_path` or `document_url` metadata
- **Storage**: In-memory vector store (NumPy)
- **Tests**: 11 unit + 3 integration

### Reducto
- **Type**: Document preprocessing + RAG completion
- **Components**: Reducto API + external embeddings + external LLM
- **Parsing**: Variable-size semantic chunking
- **Features**: Embedding-optimized output, AI enrichment, figure summarization
- **Requirements**: PDF files via `file_path` or `document_url` metadata
- **Storage**: In-memory vector store (NumPy)
- **Tests**: 11 unit + 4 integration

## Configuration Layers

1. **Human** (`config/providers.yaml`): name + api_doc_url
2. **AI** (`config/providers.generated.yaml`): detailed API specs from research
3. **Secrets** (`.env`): API keys (OPENAI_API_KEY, LLAMAINDEX_API_KEY, VISION_AGENT_API_KEY, REDUCTO_API_KEY)

## Execution Flow (Parallel Task Model)

### End-to-End Benchmark Pipeline

```
1. CLI Entry Point (scripts/run_benchmark.py)
   ├─ Parse arguments (--config, --docs, --questions, --providers, etc.)
   ├─ Load config (benchmark_qasper.yaml or benchmark_policyqa.yaml)
   └─ Create Orchestrator instance

2. Orchestrator.run_benchmark()
   ├─ Load dataset (Qasper, PolicyQA, or SQuAD 2.0)
   │  ├─ Qasper: Download metadata from HuggingFace, PDFs from arxiv (cached)
   │  ├─ PolicyQA: Download JSON from GitHub, convert HTML→PDF via Playwright (cached)
   │  └─ SQuAD 2.0: Download JSON from HuggingFace (cached)
   ├─ Create timestamped run directory
   ├─ Initialize adapters via AdapterFactory
   │  ├─ LlamaIndex (if configured)
   │  ├─ LandingAI (if configured)
   │  └─ Reducto (if configured)
   ├─ Create semaphores for rate limiting
   │  ├─ Per-provider semaphores (max_per_provider_workers=3)
   │  └─ RAGAS evaluation semaphore (max_ragas_workers=5)
   └─ Generate and execute (provider, document) task combinations

3. Parallel Task Execution (ThreadPoolExecutor)
   ├─ Create all (provider, doc) combinations as independent tasks
   ├─ Execute tasks in parallel (max_total_workers=9)
   │  ├─ Task 1: Provider A + Doc 1
   │  ├─ Task 2: Provider B + Doc 1
   │  ├─ Task 3: Provider C + Doc 1
   │  ├─ Task 4: Provider A + Doc 2
   │  └─ ... (all combinations execute concurrently)
   └─ Results collected as tasks complete (async)

4. ProviderExecutor.execute(provider, document, questions) WITH RATE LIMITING
   ├─ Acquire provider semaphore (wait if provider at capacity)
   ├─ Prepare document with PDF path metadata
   ├─ Ingest document → get index_id (with timeout)
   ├─ Query all questions → collect RAGResponse objects
   ├─ Acquire RAGAS semaphore (wait if evaluation queue full)
   ├─ Evaluate with Ragas → get metrics
   │  ├─ Faithfulness (answer grounded in context?)
   │  ├─ Factual Correctness (answer matches ground truth?)
   │  └─ Context Recall (relevant context retrieved?)
   ├─ Release RAGAS semaphore
   ├─ Release provider semaphore
   ├─ Track costs (tokens, API calls)
   └─ Return ProviderResult

5. ResultSaver.save_results() (thread-safe with locks)
   ├─ Save per-provider JSON files (as tasks complete)
   │  ├─ docs/1909.00694/llamaindex.json
   │  ├─ docs/1909.00694/landingai.json
   │  └─ docs/1909.00694/reducto.json
   ├─ Aggregate results per document (after all providers complete)
   ├─ Generate summary.json (aggregated metrics)
   └─ Save benchmark_config.yaml snapshot
```

### Parallel Execution Model

**Task-Based Parallelism**:
- Each (provider, document) is an independent task
- Example: 3 docs × 3 providers = 9 parallel tasks
- Tasks execute concurrently up to `max_total_workers` limit
- Results saved incrementally as tasks complete

**Rate Limiting with Semaphores**:
- **Per-provider semaphore**: Limits concurrent API calls per provider (prevents overwhelming provider APIs)
- **RAGAS semaphore**: Limits concurrent OpenAI evaluation calls (prevents rate limit errors)
- Tasks wait for semaphore slots before executing critical sections

**Resume Capability**:
- Check if (provider, document) result file exists
- Skip already-completed tasks on resume
- Continue with remaining task combinations

**Error Handling**:
- Individual task failures don't stop other tasks
- Timeouts configurable per operation (ingest, query, evaluation)
- Thread-safe result saving with file locks
- Partial results preserved on interruption (Ctrl+C)

**Legacy Support**:
- DocumentProcessor class kept for backward compatibility
- New code uses Orchestrator.run_benchmark() directly

## Tech Stack

- **Python 3.11+**
- **Core Libraries**:
  - `llama-index-core`, `llama-index-embeddings-openai`, `llama-index-llms-openai`
  - `llama-parse` (PDF parsing for LlamaIndex)
  - `openai` (embeddings + LLM + scoring)
  - `requests` (HTTP API calls)
  - `numpy` (vector operations)
  - `ragas` (RAG evaluation metrics)
- **Testing**: `pytest` (50+ tests, unit + integration)
- **Web Research**: Playwright MCP (via Task tool)
- **Environment**: `python-dotenv` (API key management)

## Test Coverage

| Component | Unit Tests | Integration Tests | Status |
|-----------|------------|-------------------|--------|
| LlamaIndex Adapter | 11 | 3 | ✅ All passing |
| LandingAI Adapter | 11 | 3 | ✅ All passing |
| Reducto Adapter | 11 | 4 | ✅ All passing |
| SQuAD Loader | 11 | 0 | ✅ All passing |
| Orchestrator (E2E) | 0 | 1+ | ✅ Working |
| **Total** | **44+** | **11+** | **✅ 55+/55+** |

**Integration Tests Include:**
- Individual adapter tests (ingest + query + health)
- End-to-end evaluation tests (RAG + Ragas)
- Orchestrator tests (multi-provider parallel execution)
- Resume capability validation

## Development Principles

1. **NO IMAGINATION**: All implementations based on actual API documentation
2. **Web Research First**: Use subagent to read API docs, save to `local_docs/`
3. **BaseAdapter Interface**: Standardized interface for all providers
4. **Comprehensive Testing**: Unit (mocked) + integration (real API) tests
5. **Cost-Conscious**: Use small test documents, mark integration tests with `@pytest.mark.integration`
