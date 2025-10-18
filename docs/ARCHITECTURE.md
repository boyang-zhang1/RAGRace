# RAGRace Architecture

## Components

### Core Pipeline (`src/core/`)
- **orchestrator.py** - Main benchmark coordinator (CP5)
  - Loads configuration and datasets
  - Coordinates multi-provider parallel execution
  - Manages resume capability and partial results
  - Aggregates and saves final results
- **adapter_factory.py** - Dynamic provider instantiation (CP5)
  - Creates adapter instances from config
  - Handles provider-specific initialization
  - Manages API key injection from environment
- **provider_executor.py** - Parallel provider execution (CP5)
  - Runs multiple providers on same document
  - Handles timeouts and errors gracefully
  - Tracks costs and performance per provider
- **paper_processor.py** - Document processing logic (CP5)
  - Coordinates provider execution for one paper
  - Manages question batching
  - Saves per-paper results
- **result_saver.py** - Results management with resume (CP5)
  - Saves structured JSON results
  - Enables resume from interruptions
  - Creates timestamped run directories
  - Generates summary aggregations
- **schemas.py** - Data structures (CP5)
  - BenchmarkConfig, PaperResult, ProviderResult
  - Standardized result format across providers
- **ragas_evaluator.py** - Ragas metric evaluation
  - Faithfulness, Factual Correctness, Context Recall
  - Batch evaluation for efficiency
- **scorer.py** - Batch LLM scoring (GPT structured outputs)
  - Legacy scorer for comparison
- **rag_logger.py** - Structured logging for multi-paper experiments

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

## Execution Flow (CP5 Complete)

### End-to-End Benchmark Pipeline

```
1. CLI Entry Point (scripts/run_benchmark.py)
   ├─ Parse arguments (--papers, --questions, --providers, etc.)
   ├─ Load benchmark.yaml config
   └─ Create Orchestrator instance

2. Orchestrator.run_benchmark()
   ├─ Load dataset (Qasper or SQuAD 2.0)
   │  ├─ Download metadata from HuggingFace (cached)
   │  └─ Download PDFs from arxiv on-demand (cached)
   ├─ Create timestamped run directory
   ├─ Initialize adapters via AdapterFactory
   │  ├─ LlamaIndex (if configured)
   │  ├─ LandingAI (if configured)
   │  └─ Reducto (if configured)
   └─ Process papers sequentially (or parallel if configured)

3. PaperProcessor.process_paper(paper, providers)
   ├─ Check if paper already processed (resume capability)
   ├─ Create paper directory in results/
   ├─ Execute providers IN PARALLEL (ThreadPoolExecutor)
   │  ├─ Provider 1: ingest → query all questions → evaluate
   │  ├─ Provider 2: ingest → query all questions → evaluate
   │  └─ Provider 3: ingest → query all questions → evaluate
   └─ Save per-paper results

4. ProviderExecutor.execute(provider, paper, questions)
   ├─ Prepare document with PDF path metadata
   ├─ Ingest document → get index_id (with timeout)
   ├─ Query all questions → collect RAGResponse objects
   ├─ Evaluate with Ragas → get metrics
   │  ├─ Faithfulness (answer grounded in context?)
   │  ├─ Factual Correctness (answer matches ground truth?)
   │  └─ Context Recall (relevant context retrieved?)
   ├─ Track costs (tokens, API calls)
   └─ Return ProviderResult

5. ResultSaver.save_results()
   ├─ Save per-provider JSON files
   │  ├─ papers/1909.00694/llamaindex_results.json
   │  ├─ papers/1909.00694/landingai_results.json
   │  └─ papers/1909.00694/reducto_results.json
   ├─ Generate summary.json (aggregated metrics)
   └─ Save benchmark_config.yaml snapshot
```

### Parallel Execution Model

**Per Paper**:
- All 3 providers run in parallel (ThreadPoolExecutor with max_provider_workers=3)
- Each provider independently: ingests → queries → evaluates
- Results saved as soon as each provider completes

**Resume Capability**:
- Check if paper directory exists in results/run_ID/papers/
- Skip already-processed papers on resume
- Continue from next unprocessed paper

**Error Handling**:
- Provider failures don't stop other providers
- Timeouts configurable per operation (ingest, query, evaluation)
- Partial results saved on interruption (Ctrl+C)

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
