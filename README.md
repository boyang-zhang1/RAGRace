# DocAgent Arena

**Blind A/B testing for PDF parsers. Discover which parser really performs best on your documents.**

DocAgent Arena helps you evaluate PDF parsing quality through unbiased comparison. Run blind battles to compare parsers side-by-side, or do comprehensive full-document analysis. All with transparent pricing and model flexibility.

## Features

### Parse Battle Mode
Compare PDF parsers without bias using blind A/B testing:
- Select single page from your PDF
- System randomly picks 2 providers with blind labels (A vs B)
- Review side-by-side results without knowing which is which
- Submit your preference and reveal the winners
- Track battle history and community results

**7 model configurations** across **3 providers** (LlamaIndex, Reducto, LandingAI)

[Learn more about Battle Mode →](docs/BATTLE_MODE.md)

### Side-by-Side Comparison
Comprehensive full-document parsing comparison:
- Parse entire PDFs with multiple providers simultaneously
- Cost estimation before parsing
- Page-by-page navigation and comparison
- Download results in markdown format

[Learn more about Parse Comparison →](docs/PARSE_COMPARISON.md)

### RAG Benchmarking
Also supports automated RAG provider evaluation on research datasets (Qasper, PolicyQA, SQuAD 2.0) with Ragas metrics. [See RAG documentation →](docs/RAG_BENCHMARKING.md)

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- API keys for parsers you want to test (OpenAI required)

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/DocAgent-Arena.git
cd DocAgent-Arena

# Install backend
cd backend
pip install -r requirements.txt

# Install frontend
cd ../frontend
npm install
```

### Configuration

```bash
# Copy environment template
cp backend/.env.example backend/.env

# Edit backend/.env and add your API keys:
# OPENAI_API_KEY=sk-...              # Required
# LLAMAINDEX_API_KEY=llx-...         # For LlamaIndex parser
# REDUCTO_API_KEY=red-...            # For Reducto parser
# VISION_AGENT_API_KEY=va-...        # For LandingAI parser
# DATABASE_URL=postgresql://...       # For battle history (optional)
```

### Run Battle Mode

```bash
# Start backend API
cd backend
uvicorn main:app --reload

# Start frontend (in another terminal)
cd frontend
npm run dev

# Open browser
open http://localhost:3000/battle
```

**Your first battle**:
1. Upload a PDF document
2. Select model configurations for each provider
3. Pick a single page to battle
4. Click "Run Battle" - system randomly selects 2 providers
5. Review results labeled A vs B (blind)
6. Submit your preference
7. See which provider won and the costs

## Parsing Providers

| Provider | Models | Cost Range | Key Features |
|----------|--------|------------|--------------|
| **LlamaIndex** | 3 modes | $0.003 - $0.090/page | High-res OCR, adaptive tables |
| **Reducto** | 2 modes | $0.015 - $0.030/page | Semantic chunking, figure summaries |
| **LandingAI** | 2 modes | $0.015 - $0.030/page | 8 chunk types, grounding metadata |

[Full pricing guide →](docs/PRICING.md) | [Provider details →](docs/PARSING_PROVIDERS.md)

## Architecture

```
DocAgent-Arena/
├── backend/              # FastAPI + Python parsing engine
│   ├── main.py           # API entry point
│   ├── api/              # REST endpoints (battle, parsing, RAG)
│   ├── src/adapters/     # Parsing & RAG adapters
│   └── config/           # Provider configs, pricing
├── frontend/             # Next.js 16 web interface
│   ├── app/battle/       # Battle mode UI
│   ├── app/parse/        # Side-by-side comparison
│   └── components/       # React components
└── docs/                 # Documentation
```

[Full architecture →](docs/ARCHITECTURE.md)

## Documentation

### User Guides
- **[Quick Start](docs/QUICK_START.md)** - 5-minute getting started
- **[Battle Mode](docs/BATTLE_MODE.md)** - Blind A/B testing guide
- **[Parse Comparison](docs/PARSE_COMPARISON.md)** - Full document comparison
- **[Pricing Guide](docs/PRICING.md)** - Cost calculator and optimization

### Technical Reference
- **[Parsing Providers](docs/PARSING_PROVIDERS.md)** - Parser specifications
- **[Architecture](docs/ARCHITECTURE.md)** - System design
- **[Development](docs/DEVELOPMENT.md)** - Adding new parsers
- **[RAG Benchmarking](docs/RAG_BENCHMARKING.md)** - Dataset evaluation

## Technology Stack

**Backend**: FastAPI, Prisma ORM, Supabase PostgreSQL, Python 3.11+
**Frontend**: Next.js 16, TypeScript, Tailwind CSS, shadcn/ui
**Parsers**: LlamaIndex, Reducto, LandingAI APIs

## Development

Want to add a new PDF parser?

```bash
# 1. Add to config
echo "your_parser:\n  api_doc_url: https://docs.example.com" >> backend/config/providers.yaml

# 2. Research actual API (NO IMAGINATION)
# Use web-research-gatherer subagent to read docs

# 3. Implement adapter
# Extend BaseParseAdapter in backend/src/adapters/parsing/

# 4. Add pricing
# Update backend/config/parsing_pricing.yaml

# 5. Test
pytest tests/test_yourparser.py -v
```

[Full development guide →](docs/DEVELOPMENT.md)

## Contributing

Contributions welcome! Please:
- Follow the BaseAdapter interface
- Base implementations on actual API documentation (NO IMAGINATION rule)
- Include unit and integration tests
- Update pricing configuration
- Update documentation

## License

MIT License

## Contact

For questions or issues, please open a GitHub issue.
