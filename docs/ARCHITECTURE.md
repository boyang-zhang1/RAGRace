# RAGRace Architecture

## Components

### Core (`src/core/`)
- **orchestrator.py** - Main workflow coordinator
- **adapter_factory.py** - Creates adapter instances
- **scorer.py** - Batch LLM scoring (GPT structured outputs)
- **ragas_evaluator.py** - Ragas metric evaluation (faithfulness, factual correctness, context recall)
- **rag_logger.py** - Structured logging for multi-paper RAG experiments

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

**Model**: gpt-5-mini with structured outputs

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

## Execution Flow (Current Implementation)

```
1. Load configs (providers.yaml + providers.generated.yaml)
2. Initialize adapters (LlamaIndex, LandingAI, Reducto)
3. Load dataset → preprocess (SQuAD 2.0 → DatasetSample format)
4. Ingest docs to each provider → get index_ids
5. Query all providers → collect RAGResponse objects
6. Score with batch GPT or Ragas → get metrics
7. Aggregate → compare performance
```

**Status**: Steps 1-5 working, step 6-7 need testing/integration

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
| **Total** | **44** | **10** | **✅ 54/54** |

## Development Principles

1. **NO IMAGINATION**: All implementations based on actual API documentation
2. **Web Research First**: Use subagent to read API docs, save to `local_docs/`
3. **BaseAdapter Interface**: Standardized interface for all providers
4. **Comprehensive Testing**: Unit (mocked) + integration (real API) tests
5. **Cost-Conscious**: Use small test documents, mark integration tests with `@pytest.mark.integration`
