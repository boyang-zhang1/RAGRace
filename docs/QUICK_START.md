# Quick Start Guide

Get DocAgent Arena running and complete your first PDF parser battle in 5 minutes.

## Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API key (required)
- Optional: LlamaIndex, Reducto, or LandingAI keys

## 1. Installation (2 minutes)

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

## 2. Configuration (1 minute)

```bash
# Backend configuration
cd backend
cp .env.example .env

# Edit .env and add your API key(s):
# OPENAI_API_KEY=sk-...              # Required
# LLAMAINDEX_API_KEY=llx-...         # Optional
# REDUCTO_API_KEY=red-...            # Optional
# VISION_AGENT_API_KEY=va-...        # Optional

# Frontend configuration (optional)
cd ../frontend
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

**Note**: You can test with just OpenAI key. Add other keys to enable more parsers.

## 3. Start Services (1 minute)

Open two terminal windows:

**Terminal 1 - Backend**:
```bash
cd backend
uvicorn main:app --reload
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm run dev
```

Wait for both to start:
- Backend: `Application startup complete`
- Frontend: `Local: http://localhost:3000`

## 4. Your First Battle (1 minute)

1. **Open Battle Mode**
   - Navigate to http://localhost:3000/battle

2. **Upload PDF**
   - Drag and drop any PDF document
   - Or click to browse files
   - Wait for page count

3. **Configure Models**
   - Select parse mode for each provider
   - Example: LlamaIndex "Cost-effective", Reducto "Standard"
   - Models you configure will be in the random pool

4. **Select Page**
   - Use page navigator to pick an interesting page
   - Choose pages with text, tables, or figures

5. **Run Battle**
   - Click "Run Battle"
   - Watch robot battle animation
   - Wait ~10-30 seconds for parsing

6. **Review Results**
   - See side-by-side comparison (Provider A vs B)
   - Labels are randomized - you don't know which is which!

7. **Submit Feedback**
   - Click which result is better (or both good/bad)
   - Optionally add comment
   - Click "Submit Feedback"

8. **See Winner**
   - Providers revealed
   - Costs displayed
   - Battle saved to history

## Next Steps

### Try Side-by-Side Comparison

Parse full documents with all providers:

```bash
# Navigate to http://localhost:3000/parse
# 1. Upload PDF
# 2. Select providers
# 3. Review cost estimate
# 4. Parse and compare
```

[Full guide →](PARSE_COMPARISON.md)

### Browse Battle History

```bash
# Navigate to http://localhost:3000/battle
# Scroll down to see "Battle History"
# Click any battle to see details
```

### Enable Database (Optional)

To persist battles across server restarts:

```bash
# Add to backend/.env
DATABASE_URL=postgresql://user:pass@host:5432/docagent_arena

# Apply schema
cd backend
prisma generate
prisma db push
```

Without database, battles persist only during server runtime.

### Add More Parsers

Get API keys for additional providers:

- **LlamaIndex**: https://cloud.llamaindex.ai/
- **Reducto**: https://reducto.ai/
- **LandingAI**: https://landing.ai/

Add keys to `backend/.env` and restart backend.

## Common Issues

### "Connection refused" error
- Make sure backend is running: `curl http://localhost:8000/api/health`
- Check frontend `.env.local` has correct API URL

### "Unauthorized" or "Invalid API key"
- Verify API keys in `backend/.env`
- Remove quotes around keys
- Check for trailing spaces

### "Provider not available"
- That provider's API key not set in `.env`
- Configure only providers with valid keys
- At least one provider key required (OpenAI counts for LlamaIndex)

### Battle doesn't start
- Check browser console for errors (F12)
- Verify backend logs for API errors
- Try a different PDF or page

### Parsing takes too long
- Normal: 10-60 seconds depending on page complexity
- LlamaIndex Agentic mode can take 60+ seconds
- Try "Cost-effective" modes for faster results

## Cost Estimates

Typical costs for first battle (1 page):

| Configuration | Est. Cost | Time |
|--------------|-----------|------|
| 2 × Cost-effective | $0.006 | ~15s |
| 2 × Standard | $0.030 | ~20s |
| 2 × High-quality | $0.120 | ~40s |

**Tip**: Start with cost-effective modes to test the system.

## What's Next?

- **[Battle Mode Guide](BATTLE_MODE.md)** - Deep dive into blind testing
- **[Pricing Guide](PRICING.md)** - Understanding costs and optimization
- **[Parsing Providers](PARSING_PROVIDERS.md)** - Provider specifications
- **[Architecture](ARCHITECTURE.md)** - How DocAgent-Arena works

## Getting Help

- **Documentation**: Check docs/ directory for detailed guides
- **API Docs**: http://localhost:8000/docs (when backend running)
- **Issues**: Open a GitHub issue
- **Logs**: Check terminal output for error messages

## Summary

You've successfully:
- ✅ Installed DocAgent Arena
- ✅ Configured API keys
- ✅ Started backend and frontend
- ✅ Run your first battle
- ✅ Submitted feedback and saw results

Now explore battle history, try side-by-side comparison, or run RAG benchmarks!
