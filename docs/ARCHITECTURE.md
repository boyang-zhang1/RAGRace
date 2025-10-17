# RAGRace Architecture

## Components

### Core (`src/core/`)
- **orchestrator.py** - Main workflow coordinator
- **adapter_factory.py** - Creates adapter instances
- **scorer.py** - Batch LLM scoring (GPT structured outputs)

### Adapters (`src/adapters/`)
- **base.py** - BaseAdapter interface (ALL providers must implement)
- **{provider}.py** - Generated adapters (from API docs via Playwright)

### Datasets (`src/datasets/`)
- **loader.py** - Load datasets
- **preprocessors/*.py** - Dataset-specific preprocessing

### API Discovery (`src/api_discovery/`)
- **doc_reader.py** - Playwright MCP → read docs → extract API structure
- **adapter_generator.py** - Generate adapter code from API docs

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

## Configuration Layers

1. **Human** (`config/providers.yaml`): name + api_doc_url
2. **AI** (`config/providers.generated.yaml`): full API spec from Playwright
3. **Secrets** (`.env`): API keys

## Execution Flow

```
1. Load configs
2. API Discovery: Playwright reads docs → generate adapters
3. Load dataset → preprocess
4. Ingest docs to all RAG providers → get index_ids
5. Query all providers → collect predictions
6. Batch score with GPT → get scores
7. Aggregate → export results
```

## Tech Stack

- Python 3.10+, Pydantic, AsyncIO
- Playwright MCP (doc reading)
- OpenAI (scoring)
- pytest (testing)
