# RAGRace

A comprehensive platform for comparing and benchmarking different RAG (Retrieval-Augmented Generation) APIs and services.

## Overview

RAGRace provides a standardized framework to evaluate and compare RAG providers using unified interfaces and automated scoring. The platform supports multiple providers with a consistent `BaseAdapter` interface for fair, apples-to-apples comparison.

**Current Status**: 3 RAG providers integrated with 54+ passing tests. Complete end-to-end evaluation on Qasper dataset (1,585 research papers with 5,049 questions).

## Integrated Providers

| Provider | Type | Key Features | Status |
|----------|------|--------------|--------|
| **[LlamaIndex](docs/ADAPTERS.md#llamaindex)** | Full RAG Framework | VectorStoreIndex, built-in embeddings | ✅ Tested |
| **[LandingAI](docs/ADAPTERS.md#landingai-ade-agentic-document-extraction)** | Doc Preprocessing | 8 chunk types, grounding metadata | ✅ Tested |
| **[Reducto](docs/ADAPTERS.md#reducto)** | Doc Preprocessing | Embedding-optimized, AI enrichment | ✅ Tested |

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/RAGRace.git
cd RAGRace

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Add your API keys to .env
OPENAI_API_KEY=your_openai_key_here
VISION_AGENT_API_KEY=your_landingai_key_here  # For LandingAI
REDUCTO_API_KEY=your_reducto_key_here          # For Reducto
```

### Basic Usage

```python
from src.adapters import LlamaIndexAdapter, Document
import os

# Initialize adapter
adapter = LlamaIndexAdapter()
adapter.initialize(api_key=os.getenv("OPENAI_API_KEY"))

# Prepare documents
docs = [
    Document(
        id="doc1",
        content="Your document text here...",
        metadata={"source": "example"}
    )
]

# Ingest documents
index_id = adapter.ingest_documents(docs)

# Query
response = adapter.query("What is this document about?", index_id)

# Get results
print(f"Answer: {response.answer}")
print(f"Context chunks: {len(response.context)}")
print(f"Latency: {response.latency_ms:.2f}ms")
```

## Datasets

RAGRace supports multiple datasets for evaluation:

| Dataset | Type | Papers | Questions | Format | Status |
|---------|------|--------|-----------|--------|--------|
| **SQuAD 2.0** | Q&A on Wikipedia | - | 150K+ | Text paragraphs | ✅ Integrated |
| **Qasper** | Q&A on Research Papers | 1,585 | 5,049 | Original PDFs from arxiv | ✅ Integrated |

### Qasper Dataset

Complete integration with original research papers:

```python
from src.datasets.loader import DatasetLoader

# Load Qasper papers with questions
dataset = DatasetLoader.load_qasper(
    split='train',
    max_papers=10,  # None = all 888 papers
    filter_unanswerable=True
)

# Each sample contains:
# - question: Research question about the paper
# - context: Raw PDF text (realistic, with formatting artifacts)
# - ground_truth: Expert-annotated answer
# - metadata: paper_id, pdf_path, question_id, etc.
```

**Features:**
- Downloads original PDFs from arxiv (cached locally)
- 888 train papers, 281 validation, 416 test
- Questions asked by regular readers, answered by NLP practitioners
- Tests RAG on long-form scientific documents (10K+ tokens)

## Running Tests

```bash
# Run unit tests (fast, no API calls)
pytest tests/ -v -k "not integration"

# Run integration tests (real API calls, costs money)
pytest tests/ -v -m integration -s

# Run RAGRace comparison on Qasper (3 providers, 1 paper, 3 questions)
pytest tests/test_qasper_rag_e2e.py -v -s -m integration
```

### RAGRace End-to-End Test

Complete 3-way provider comparison on Qasper dataset:

```bash
pytest tests/test_qasper_rag_e2e.py::TestQasperRAGRace::test_ragrace_3_providers_qasper -v -s -m integration
```

**Customize paper/question count:**

Edit `tests/test_qasper_rag_e2e.py` lines 102-103:

```python
max_papers = 1      # Change to 10 for 10 papers
max_questions = 3   # Change to None for all questions, or 10 for 10 questions
```

**Examples:**
- `max_papers=1, max_questions=3` → 1 paper, 3 questions (~2 min, $0.20)
- `max_papers=5, max_questions=10` → 5 papers, 10 questions per paper (~15 min, $2)
- `max_papers=10, max_questions=None` → 10 papers, ALL questions (~30 min, $5)
- `max_papers=None, max_questions=None` → ALL 888 papers, ALL questions (EXPENSIVE!)

## Project Structure

```
RAGRace/
├── src/
│   ├── adapters/          # RAG provider adapters
│   │   ├── base.py        # BaseAdapter interface
│   │   ├── llamaindex_adapter.py
│   │   ├── landingai_adapter.py
│   │   └── reducto_adapter.py
│   ├── core/              # Scoring and evaluation
│   └── datasets/          # Dataset loaders
├── tests/                 # Unit and integration tests
├── config/                # Provider configurations
├── docs/                  # Documentation
│   ├── ARCHITECTURE.md    # System architecture
│   ├── ADAPTERS.md        # Adapter specifications
│   └── DEVELOPMENT.md     # Development guide
└── data/                  # Datasets and results
```

## Documentation

- **[Architecture](docs/ARCHITECTURE.md)** - System design and components
- **[Adapter Reference](docs/ADAPTERS.md)** - Detailed adapter specs and comparison
- **[Development Guide](docs/DEVELOPMENT.md)** - How to add new providers
- **[Project Plan](local_docs/PROJECT_PLAN.md)** - Development roadmap (AI continuity)

## Key Features

- ✅ **Standardized Interface**: All providers implement `BaseAdapter` for fair comparison
- ✅ **Comprehensive Testing**: 54+ tests with real API validation
- ✅ **Multiple Providers**: LlamaIndex, LandingAI, Reducto (more coming)
- ✅ **Dataset Support**: SQuAD 2.0 + Qasper (research papers) with Ragas evaluation
- ✅ **End-to-End RAGRace**: Complete 3-way comparison on original PDFs
- ✅ **Fair Evaluation**: All providers tested on SAME PDF format with SAME questions
- ✅ **Web Research**: Uses Playwright MCP to read actual API documentation

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
