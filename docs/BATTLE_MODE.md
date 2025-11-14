# Parse Battle Mode

Blind A/B testing for PDF parsers. Discover which parser really performs best without confirmation bias.

## Overview

Battle Mode lets you compare PDF parsers through unbiased blind testing. The system randomly selects two providers, assigns anonymous labels (A vs B), and lets you judge quality based solely on results - not brand names.

### Why Blind Testing?

- **Eliminates brand bias**: Judge results without knowing provider names
- **Reveals true quality**: Focus on output, not marketing claims
- **Cost-conscious**: Single-page battles keep costs low ($0.003-$0.18 per battle)
- **Build intuition**: Learn what "good" parsing looks like through practice
- **Track history**: Compare your judgments with costs and configurations

### Key Features

- 🎲 Random provider selection from configured pool
- 🔒 Blind labels prevent bias
- 📄 Single-page battles minimize cost
- 🤖 Animated robot battles during parsing
- 💾 Battle history with feedback
- 💰 Transparent pricing after reveal
- 🏆 Winner tracking

## How It Works

### Battle Flow

```
1. Upload PDF → 2. Configure Models → 3. Select Page →
4. Run Battle (random 2 providers) → 5. Review Blind Results →
6. Submit Preference → 7. Reveal Winners
```

### Technical Process

1. **Provider Pool Selection**: You configure which parsers and modes to include
2. **Random Selection**: System picks 2 from available providers
3. **Label Randomization**: Providers assigned to labels A/B in random order
4. **Single Page Extraction**: Temporary PDF created with just the selected page
5. **Parallel Parsing**: Both providers parse simultaneously
6. **Blind Presentation**: Results shown side-by-side with anonymous labels
7. **Feedback Collection**: You choose winner or judge both equal
8. **Storage & Reveal**: Battle saved to database/storage, providers revealed

## Using Battle Mode

### Step 1: Upload PDF

```
Navigate to: http://localhost:3000/battle
```

- **Drag and drop** any PDF document
- Or **click to browse** your files
- System analyzes and returns page count
- Supports any PDF size (recommended: < 100 pages for UI performance)

**Tips**:
- Choose PDFs with diverse content (text, tables, figures, equations)
- Research papers, financial reports, and technical docs work well
- Avoid image-only scans (all parsers struggle equally)

### Step 2: Configure Model Options

For each provider, select your preferred parsing mode:

#### LlamaIndex Options

| Mode | Model | Credits/Page | Cost/Page | Speed | Best For |
|------|-------|--------------|-----------|-------|----------|
| **Cost-effective** | GPT-4o-mini | 3 | $0.003 | Fast | General documents |
| **Agentic** | GPT-4o-mini | 10 | $0.010 | Medium | Complex layouts |
| **Agentic Plus** | Sonnet 4.0 | 90 | $0.090 | Slow | Maximum quality |

#### Reducto Options

| Mode | Credits/Page | Cost/Page | Speed | Best For |
|------|--------------|-----------|-------|----------|
| **Standard** | 1 | $0.015 | Fast | Clean documents |
| **Complex VLM** | 2 | $0.030 | Medium | Figures, diagrams |

#### LandingAI Options

| Mode | Credits/Page | Cost/Page | Speed | Best For |
|------|--------------|-----------|-------|----------|
| **DPT-2 Mini** | 1.5 | $0.015 | Fast | General use |
| **DPT-2** | 3 | $0.030 | Medium | Detailed extraction |

**Configuration Strategy**:
- Select ALL providers/modes you want to test
- Only configured options enter the random pool
- Battle randomly picks 2 from your selection
- Different modes of same provider can battle each other!

### Step 3: Pick a Page

Use the page navigator to select one page for the battle:

**Navigation**:
- **Arrow buttons**: Previous/next page
- **Page input**: Jump directly to page number
- **PDF Preview**: Shows selected page (if available)

**Page Selection Tips**:
- **Page 1**: Often has titles/headers (easy parsing)
- **Middle pages**: Typical content density
- **Table pages**: Good for testing structure preservation
- **Figure pages**: Tests image/caption handling
- **Equation pages**: Challenges OCR capabilities
- **Multi-column**: Tests layout understanding

**Strategy**: Rotate through different page types to build comprehensive understanding of each parser's strengths.

### Step 4: Run Battle

Click **"Run Battle"** to start the blind comparison.

**What Happens**:
1. System randomly selects 2 providers from your configured pool
2. Creates temporary single-page PDF from selected page
3. Assigns blind labels (Provider A, Provider B) in random order
4. Starts parsing both providers in parallel
5. Shows animated robot battle during processing

**Duration**: 10-60 seconds depending on:
- Page complexity
- Selected modes (Agentic modes take longer)
- Provider API response times

**Visual Feedback**:
- Robot animation indicates parsing in progress
- Loading spinner for each provider
- Error messages if parsing fails

### Step 5: Review Blind Results

Results displayed side-by-side with anonymous labels:

```
┌─────────────────┬─────────────────┐
│  Provider A     │  Provider B     │
├─────────────────┼─────────────────┤
│  (markdown)     │  (markdown)     │
│  (preview)      │  (preview)      │
└─────────────────┴─────────────────┘
```

**Evaluation Criteria**:
- **Accuracy**: Is the text correct?
- **Structure**: Are headings, lists, tables preserved?
- **Formatting**: Is markdown clean and readable?
- **Completeness**: Any missing content?
- **Tables**: Are tables properly formatted?
- **Equations**: Are mathematical formulas preserved?
- **Figures**: Are captions and context included?

**Tips**:
- Scroll both sides in parallel
- Check table alignment carefully
- Look for missing or hallucinated text
- Evaluate markdown cleanliness
- Consider both accuracy AND formatting

### Step 6: Submit Feedback

Choose your preference:

- **Left is better** - Provider A wins
- **Right is better** - Provider B wins
- **Both are good** - Tie, both performed well
- **Both are bad** - Tie, both performed poorly

**Optional Comment**: Add notes about why you chose the winner.

**Feedback Examples**:
- "Left preserved table structure, right merged columns"
- "Right has cleaner markdown, but left is more accurate"
- "Both good, minimal differences"
- "Both missed the equation block entirely"

### Step 7: Reveal & Results

After submitting feedback:

**Reveals**:
- Provider names unmasked (which was A, which was B)
- Model configurations used
- Processing times
- Costs per provider

**Winner Display**:
- 🏆 Winner highlighted with trophy icon
- 👍 "Both good" shows double checkmarks
- 👎 "Both bad" shows warning icon
- 💰 Cost breakdown displayed

**Battle Saved**:
- Stored in database (if configured)
- Accessible in Battle History
- Includes PDF, results, and feedback

## Battle History

View all past battles at the bottom of the battle page.

### History List

Shows recent battles with:
- Battle ID and timestamp
- Provider names and models
- Your feedback (winner or tie)
- Costs and processing times

**Pagination**: 10 battles per page, click "Load More" for older battles.

### Battle Detail View

Click any battle to see full replay:
- Original PDF page preview
- Side-by-side comparison (revealed)
- Winner highlighted
- Your feedback comment
- Full cost and timing breakdown
- Model display names

**Use Cases**:
- Review past decisions
- Compare costs across configurations
- Learn from your evaluations
- Share results with team

## Advanced Usage

### Testing Specific Matchups

Want to compare two specific providers?

**Technique**: Configure only those 2 providers

```
Example: LlamaIndex Cost-effective vs Reducto Standard
1. Enable only:
   - LlamaIndex: Cost-effective
   - Reducto: Standard
2. All other options: Disabled
3. Run battle
→ Guaranteed matchup between these two
```

### Mode Comparison Within Provider

Compare modes of the same provider:

```
Example: LlamaIndex Cost-effective vs Agentic
1. Enable only:
   - LlamaIndex: Cost-effective
   - LlamaIndex: Agentic
2. Other providers: Disabled
3. Run battle
→ Blind test of same provider's modes
```

### Building a Personal Ranking

Develop your own parser ranking:

1. **Run 10+ battles** with diverse page types
2. **Track win rates** per provider/mode
3. **Note patterns**: Which wins tables? Figures? Equations?
4. **Consider cost**: Best value for your use case?
5. **Match to needs**: Pick parser based on doc types

### Cost Optimization Strategy

Find the cheapest parser that meets your quality bar:

1. **Baseline**: Run battles with all providers
2. **Identify winners**: Which provider(s) typically win?
3. **Test cheaper modes**: Can cheaper modes achieve similar quality?
4. **Document-specific**: Different parsers for different doc types?

**Example Findings**:
- "Reducto Standard wins 70% on our technical docs"
- "LlamaIndex Cost-effective sufficient for simple reports"
- "LandingAI DPT-2 needed only for complex forms"

## Database Persistence

### With Database (Recommended)

Configure `DATABASE_URL` in `backend/.env`:

```bash
DATABASE_URL=postgresql://user:pass@host:5432/docagent_arena
```

**Benefits**:
- Battles persist across server restarts
- Battle history available indefinitely
- PDF storage in Supabase (public URLs)
- Query battle data for analytics

**Schema**: `ParseBattleRun`, `BattleProviderResult`, `BattleFeedback`

### Without Database (Temporary)

Battles stored in-memory only:

- **Persists**: During server runtime
- **Lost**: On server restart
- **Suitable**: Testing, development
- **Limitation**: No persistent history

## Cost Management

### Per-Battle Costs

Cost = (Provider 1 cost) + (Provider 2 cost)

**Example Calculations**:

```
Battle: LlamaIndex Cost-effective vs Reducto Standard (1 page)
= $0.003 + $0.015
= $0.018 per battle

Battle: LlamaIndex Agentic Plus vs Reducto Complex VLM (1 page)
= $0.090 + $0.030
= $0.120 per battle
```

### Budget Planning

| Budget | Battles @ Avg Cost | Strategy |
|--------|-------------------|----------|
| $1 | 55 battles @ $0.018 | Cost-effective modes only |
| $5 | 100 battles @ mixed | 70% cheap, 30% expensive |
| $20 | 166 battles @ mixed | Test all modes extensively |

### Cost Tracking

After each battle:
- Total cost displayed
- Per-provider breakdown
- Credits used shown
- Processing time noted

**Monitor**: Check battle history to analyze spending patterns.

## Technical Details

### Random Selection Algorithm

```python
def _select_battle_providers(configured_providers: list) -> tuple:
    """Select 2 providers randomly from configured pool."""
    if len(configured_providers) < 2:
        raise ValueError("Need at least 2 providers configured")

    selected = random.sample(configured_providers, 2)
    # Randomize label assignment
    labels = ['A', 'B']
    random.shuffle(labels)

    return {
        labels[0]: selected[0],
        labels[1]: selected[1]
    }
```

**Key Properties**:
- Uniform random selection
- No replacement (2 different providers)
- Label assignment also randomized
- Completely unbiased

### Single-Page PDF Extraction

Temporary PDF created with just the selected page:

```python
def _extract_single_page(pdf_path: Path, page_number: int) -> Path:
    """Extract single page to temporary PDF."""
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    writer.add_page(reader.pages[page_number - 1])  # 0-indexed

    temp_path = TEMP_DIR / f"{uuid4()}_page{page_number}.pdf"
    with open(temp_path, 'wb') as f:
        writer.write(f)

    return temp_path
```

**Benefits**:
- Faster parsing (1 page vs full doc)
- Lower costs (proportional to pages)
- Focused comparison
- Same result quality as full doc

### Async Battle Persistence

Battle saved asynchronously without blocking response:

```python
async def _save_battle_to_db(battle_data: dict):
    """Fire-and-forget battle persistence."""
    # Upload PDF to Supabase storage
    # Create ParseBattleRun record
    # Create BattleProviderResult records
    # Link battle_id to results
```

**User Experience**:
- Instant reveal after feedback
- No waiting for database save
- Battle history available shortly after

### Storage Architecture

**With Supabase**:
- Single-page PDFs uploaded to cloud storage
- Public URLs generated for viewing
- Battle records in PostgreSQL
- Files never deleted (permanent history)

**Without Supabase**:
- PDFs in temporary directory (`/tmp`)
- Cleaned up on server restart
- No permanent storage

## Best Practices

### For Researchers

- **Diverse battles**: Test different doc types and page types
- **Track findings**: Export battle history for analysis
- **Control variables**: Compare same page across battles
- **Sample size**: 20+ battles per provider for statistical significance

### For Developers

- **Test modes**: Use battles to test new parser configurations
- **Cost optimization**: Find cheapest acceptable quality
- **Edge cases**: Battle on problematic pages to identify weaknesses
- **Benchmarking**: Systematic battles across doc corpus

### For Teams

- **Shared feedback**: Multiple team members battle same docs
- **Consensus building**: Compare judgments in battle history
- **Knowledge sharing**: Comments explain evaluation criteria
- **Standard setting**: Define quality bar through examples

## Troubleshooting

### Battle Doesn't Start

**Issue**: Click "Run Battle" but nothing happens

**Solutions**:
- Check at least 2 providers configured
- Verify API keys in `backend/.env`
- Check browser console (F12) for errors
- Review backend logs for API failures

### One Provider Fails

**Issue**: Only one result shows, other side blank/error

**Solutions**:
- Check that provider's API key validity
- Review backend logs for specific error
- Try different page (some pages may challenge specific parsers)
- Verify sufficient API credits/quota

### Results Look Identical

**Issue**: Both sides show same or very similar output

**Possibilities**:
- Parsers performed equally well (legitimate)
- Simple page with minimal parsing challenge
- Both using same underlying model (e.g., both use GPT for synthesis)

**Action**: Try more complex page (tables, figures, equations)

### Costs Higher Than Expected

**Issue**: Battle costs more than estimate

**Causes**:
- Agentic modes use variable credits (10-90 range)
- Complex pages may trigger higher credit usage
- Pricing configuration mismatch

**Check**: Review actual credits used in battle results

### Database Errors

**Issue**: Battle succeeds but history doesn't show

**Solutions**:
- Verify `DATABASE_URL` in `.env`
- Run `prisma db push` to apply schema
- Check database connection: `prisma studio`
- Review backend logs for save errors

## API Reference

Battle endpoints in `backend/api/routers/parsing.py`:

### Run Battle

```http
POST /api/v1/parsing/compare
Content-Type: application/json

{
  "file_id": "uuid-string",
  "page_number": 5,
  "providers": [],  // Empty = random selection
  "api_keys": {
    "llamaindex": "llx-...",
    "reducto": "red-...",
    "landingai": "va-..."
  },
  "configs": {
    "llamaindex": { "parse_mode": "parse_page_with_llm", "model": "openai-gpt-4-1-mini" },
    "reducto": { "mode": "standard", "summarize_figures": false },
    "landingai": { "model": "dpt-2-latest" }
  }
}
```

**Response**:
```json
{
  "battle_id": "uuid",
  "assignments": {
    "A": "llamaindex",
    "B": "reducto"
  },
  "results": {
    "A": { "markdown": "...", "cost": 0.003, "time_ms": 1234 },
    "B": { "markdown": "...", "cost": 0.015, "time_ms": 2345 }
  }
}
```

### Submit Feedback

```http
POST /api/v1/parsing/battle-feedback
Content-Type: application/json

{
  "battle_id": "uuid",
  "preferred_labels": ["A"],  // or ["B"], or ["A", "B"], or []
  "comment": "Left had better table formatting"
}
```

### Get Battle History

```http
GET /api/v1/parsing/battles?limit=10&offset=0
```

### Get Battle Detail

```http
GET /api/v1/parsing/battles/{battle_id}
```

## Related Documentation

- **[Quick Start](QUICK_START.md)** - Get battle mode running in 5 minutes
- **[Pricing Guide](PRICING.md)** - Detailed cost breakdown and optimization
- **[Parsing Providers](PARSING_PROVIDERS.md)** - Provider specifications
- **[Architecture](ARCHITECTURE.md)** - Battle system technical architecture
