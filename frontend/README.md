# DocAgent Arena Frontend

Next.js web interface for PDF parser comparison and RAG benchmarking.

## Overview

Three main features:
1. **Parse Battle** (`/battle`) - Blind A/B testing of PDF parsers
2. **Side-by-Side Comparison** (`/parse`) - Full document parsing comparison
3. **RAG Results** (`/`, `/results/[id]`) - Browse RAG benchmark results

## Prerequisites

- Node.js 18+ and npm
- Backend API running at `http://localhost:8000`

## Quick Start

```bash
# Install dependencies
npm install

# Configure API URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start development server
npm run dev

# Open http://localhost:3000
```

## Project Structure

```
frontend/
├── app/
│   ├── battle/           # Parse Battle UI
│   │   ├── page.tsx      # Battle mode main page + history
│   │   └── [battleId]/   # Battle detail view
│   ├── parse/            # Side-by-side comparison
│   │   └── page.tsx      # Full document parsing
│   ├── results/          # RAG benchmark results
│   │   └── [run_id]/     # Run detail view
│   └── datasets/         # Dataset information
│
├── components/
│   ├── parse/            # Parsing UI components
│   │   ├── FileUploadZone.tsx
│   │   ├── ApiKeyForm.tsx
│   │   ├── CostEstimation.tsx
│   │   ├── PDFViewer.tsx
│   │   └── MarkdownViewer.tsx
│   ├── results/          # RAG results components
│   └── ui/               # shadcn/ui components
│
├── lib/
│   ├── api-client.ts     # Backend API client
│   └── utils.ts          # Utilities
│
└── types/
    └── api.ts            # TypeScript types
```

## Pages

### Battle Mode (`/battle`)

Blind A/B testing interface:
- Upload PDF and select page for battle
- Configure model options per provider
- View blind comparison (Provider A vs B)
- Submit feedback and reveal winners
- Browse battle history with results

**Key Components**: `BattleComparisonView`, `FeedbackForm`, `BattleHistory`, `BattleCard`

### Parse Comparison (`/parse`)

Full document parsing:
- Drag-and-drop PDF upload
- Select providers and configure options
- Cost estimation before parsing
- Page-by-page navigation
- Download results

**Key Components**: `FileUploadZone`, `ApiKeyForm`, `CostEstimation`, `PDFViewer`, `MarkdownViewer`

### Results Browser (`/`)

RAG benchmark results:
- Sortable table of benchmark runs
- Filter by dataset
- Click row to view details

### Run Details (`/results/[id]`)

Detailed benchmark analysis:
- Aggregate scores across documents
- Interactive metric charts
- Question-by-question results
- Provider comparison tables

### Datasets (`/datasets`)

Available benchmark datasets information

## API Integration

### Parsing Endpoints

```typescript
// Upload PDF
POST /api/v1/parsing/upload
FormData { file }

// Get page count
POST /api/v1/parsing/page-count
{ file_id: string }

// Run battle (single page)
POST /api/v1/parsing/compare
{
  file_id: string,
  page_number: number,
  configs: { provider: { mode, model } }
}

// Submit feedback
POST /api/v1/parsing/battle-feedback
{
  battle_id: string,
  preferred_labels: string[],
  comment: string
}

// Get battle history
GET /api/v1/parsing/battles?limit=10&offset=0

// Get battle detail
GET /api/v1/parsing/battles/{battle_id}
```

### RAG Endpoints

```typescript
// List runs
GET /api/v1/results?limit=50&offset=0

// Get run details
GET /api/v1/results/{run_id}

// Get datasets
GET /api/v1/datasets
```

See `lib/api-client.ts` for full API client implementation.

## Technology Stack

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS v3
- **UI Components**: shadcn/ui
- **Charts**: Recharts
- **Animation**: Framer Motion (battle mode)
- **Icons**: lucide-react

## Development

```bash
# Development mode with hot reload
npm run dev

# Production build
npm run build

# Start production server
npm start

# Lint
npm run lint
```

## State Management

- **API Keys**: Stored in localStorage, persisted across sessions
- **Provider Configs**: Stored in localStorage per provider
- **Battle State**: React state, cleared on page refresh
- **Parse Results**: React state, temporary

## Styling

Built with Tailwind CSS v3 and shadcn/ui components. Theme configured in `tailwind.config.js`.

## Troubleshooting

### Backend connection issues
```bash
# Check backend is running
curl http://localhost:8000/api/health

# Verify .env.local
cat .env.local
```

### Build errors
```bash
# Clean rebuild
rm -rf .next node_modules package-lock.json
npm install
npm run build
```

## Contributing

When adding features:
1. Add TypeScript types to `types/api.ts`
2. Update API client in `lib/api-client.ts`
3. Create reusable components in `components/`
4. Follow existing naming conventions (PascalCase for components)

## License

Part of the DocAgent Arena project (MIT License).
