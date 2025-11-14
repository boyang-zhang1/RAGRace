# DocAgent-Arena Development Guide

## Development Principles

1. **NO IMAGINATION**: All implementations based on actual API documentation
2. **Web Research First**: Use Playwright MCP subagent to read API docs
3. **BaseAdapter Interface**: All providers implement standardized interface
4. **Comprehensive Testing**: Unit (mocked) + integration (real API) tests
5. **Cost-Conscious**: Use small test documents for integration tests

## Adding a New RAG Provider

### 1. Add to Configuration

Edit `config/providers.yaml`:
```yaml
providers:
  - name: your_provider
    api_doc_url: https://docs.your-provider.com/
```

### 2. Research API Documentation

Launch the web-research-gatherer subagent:
```
Use Claude Code's Task tool with:
- subagent_type: general-purpose
- Task: Visit API docs and gather information about:
  - Authentication methods
  - Document ingestion endpoints
  - Query/search endpoints
  - Response formats
  - Rate limits

Create research document in local_docs/research_yourprovider_api_YYYYMMDD.md
```

**Important**: The subagent will:
- Use Playwright MCP to navigate documentation
- Extract ACTUAL API information (no guessing!)
- Save comprehensive notes to `local_docs/`
- Return the file path when complete

### 3. Implement Adapter

Create `src/adapters/yourprovider_adapter.py`:

```python
from src.adapters.base import BaseAdapter, Document, RAGResponse
import time
from typing import List, Dict, Optional

class YourProviderAdapter(BaseAdapter):
    """Adapter for YourProvider RAG API."""

    def __init__(self):
        self._initialized = False
        self._api_key = None
        # Add provider-specific state

    def initialize(self, api_key: str, **kwargs) -> None:
        """Initialize with API key and config."""
        self._api_key = api_key
        # Initialize provider client
        self._initialized = True

    def ingest_documents(self, documents: List[Document]) -> str:
        """Ingest documents and return index_id."""
        if not self._initialized:
            raise RuntimeError("Adapter not initialized")

        # Call provider API to ingest documents
        # Return index_id
        pass

    def query(self, question: str, index_id: str, **kwargs) -> RAGResponse:
        """Query the RAG system."""
        if not self._initialized:
            raise RuntimeError("Adapter not initialized")

        start_time = time.time()

        # Call provider API to query
        # Extract answer and context

        latency_ms = (time.time() - start_time) * 1000

        return RAGResponse(
            answer=answer,
            context=context_chunks,
            metadata={"index_id": index_id, ...},
            latency_ms=latency_ms
        )

    def health_check(self) -> bool:
        """Check if provider is accessible."""
        try:
            # Test API connectivity
            return True
        except Exception:
            return False
```

**Key Requirements**:
- Must implement all `BaseAdapter` methods
- Must be based on actual API documentation from research doc
- Handle errors gracefully
- Include proper logging

### 4. Update Exports

Add to `src/adapters/__init__.py`:
```python
from src.adapters.yourprovider_adapter import YourProviderAdapter

__all__ = [
    ...
    "YourProviderAdapter",
]
```

### 5. Update Generated Config

Add to `config/providers.generated.yaml`:
```yaml
yourprovider:
  name: "YourProvider"
  description: "Brief description"
  api_documentation: "https://..."

  auth:
    type: "api_key"
    env_var: "YOURPROVIDER_API_KEY"
    required: true

  endpoints:
    base_url: "https://api.yourprovider.com"
    # List endpoints

  config:
    # Configuration options

  capabilities:
    # What it can do

  dependencies:
    - "requests>=2.31.0"
    # Other dependencies

  implementation:
    class_name: "YourProviderAdapter"
    module_path: "src.adapters.yourprovider_adapter"

  notes:
    - "Important implementation notes"
```

### 6. Write Tests

Create `tests/test_yourprovider_adapter.py`:

```python
import pytest
from unittest.mock import Mock, patch
import os

from src.adapters.base import Document, RAGResponse
from src.adapters.yourprovider_adapter import YourProviderAdapter


class TestYourProviderAdapterUnit:
    """Unit tests (mocked, no API calls)."""

    def test_adapter_initialization(self):
        adapter = YourProviderAdapter()
        assert adapter is not None
        assert not adapter._initialized

    def test_initialize_success(self):
        adapter = YourProviderAdapter()
        adapter.initialize(api_key="test_key")
        assert adapter._initialized

    def test_ingest_documents_not_initialized(self):
        adapter = YourProviderAdapter()
        with pytest.raises(RuntimeError):
            adapter.ingest_documents([])

    # Add more unit tests


@pytest.mark.integration
class TestYourProviderAdapterIntegration:
    """Integration tests (real API calls)."""

    @pytest.fixture
    def api_key(self):
        key = os.getenv("YOURPROVIDER_API_KEY")
        if not key:
            pytest.skip("YOURPROVIDER_API_KEY not set")
        return key

    @pytest.fixture
    def adapter(self, api_key):
        adapter = YourProviderAdapter()
        adapter.initialize(api_key=api_key)
        return adapter

    def test_health_check(self, adapter):
        assert adapter.health_check()

    def test_end_to_end_workflow(self, adapter):
        # Test with minimal document
        docs = [Document(
            id="test",
            content="Test content",
            metadata={}
        )]

        index_id = adapter.ingest_documents(docs)
        assert index_id is not None

        response = adapter.query("Test question?", index_id)
        assert isinstance(response, RAGResponse)
        assert response.answer is not None
        assert len(response.context) > 0
```

**Testing Guidelines**:
- **Unit tests**: Fast, mocked, no API calls
- **Integration tests**: Real API calls, mark with `@pytest.mark.integration`
- **Use small test data**: Keep costs minimal
- **Run unit tests before commit**: `pytest tests/ -k "not integration"`

### 7. Update Documentation

Update these files:
- `README.md` - Add provider to list
- `docs/ARCHITECTURE.md` - Add implementation details
- `docs/ADAPTERS.md` - Add adapter specifications
- `.env.example` - Add API key placeholder

### 8. Update Environment

Add to `.env.example`:
```bash
YOURPROVIDER_API_KEY=your_api_key_here
```

## Testing Workflow

### Run Unit Tests (Fast, No API Calls)
```bash
# All unit tests
pytest tests/ -v -k "not integration"

# Specific adapter
pytest tests/test_yourprovider_adapter.py -v -k "not integration"
```

### Run Integration Tests (Real API Calls)
```bash
# All integration tests
pytest tests/ -v -m integration -s

# Specific adapter
pytest tests/test_yourprovider_adapter.py -v -m integration -s

# Single test
pytest tests/test_yourprovider_adapter.py::TestIntegration::test_health_check -v -m integration -s
```

### Run All Tests
```bash
pytest tests/ -v
```

## Code Style

- Follow PEP 8
- Use type hints
- Add docstrings for classes and methods
- Keep functions focused and small
- Handle errors explicitly

## Common Patterns

### Document Preprocessing Providers (LandingAI, Reducto)

If provider is a document preprocessing service (not full RAG):
1. Parse documents via provider API
2. Generate embeddings externally (e.g., OpenAI)
3. Store in in-memory vector store (NumPy)
4. Implement semantic search with cosine similarity
5. Use external LLM for answer generation

### Full RAG Frameworks (LlamaIndex)

If provider is a complete RAG framework:
1. Use provider's native document ingestion
2. Use provider's native embedding + storage
3. Use provider's native retrieval + generation
4. Return standardized RAGResponse

## Debugging Tips

1. **Enable verbose logging**: Add `import logging; logging.basicConfig(level=logging.DEBUG)`
2. **Check API responses**: Print response JSON to understand structure
3. **Test incrementally**: Test each method separately before end-to-end
4. **Use small data**: Start with 1-2 documents for faster iteration
5. **Check research doc**: Refer to `local_docs/research_*` for API details

## Git Workflow

### Before Committing

1. Run unit tests: `pytest tests/ -k "not integration"`
2. Run integration tests for new adapter: `pytest tests/test_newadapter.py -m integration`
3. Update documentation
4. Check that research docs are in `local_docs/` (not committed)

### Commit Files

**Include**:
- `src/adapters/newadapter.py`
- `src/adapters/__init__.py`
- `tests/test_newadapter.py`
- `config/providers.yaml`
- `config/providers.generated.yaml`
- `.env.example`
- `README.md`, `docs/*.md`

**Exclude** (already gitignored):
- `local_docs/` - Session state, research docs
- `.env` - Secrets
- `data/cache/`, `data/results/` - Runtime data

## Resources

- **BaseAdapter Interface**: `src/adapters/base.py`
- **Example Adapters**:
  - LlamaIndex: `src/adapters/llamaindex_adapter.py`
  - LandingAI: `src/adapters/landingai_adapter.py`
  - Reducto: `src/adapters/reducto_adapter.py`
- **Example Tests**: `tests/test_llamaindex_adapter.py`
- **Research Docs**: `local_docs/research_*_api_*.md`
