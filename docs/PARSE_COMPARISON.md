# Side-by-Side Parse Comparison

Comprehensive full-document parsing comparison across multiple providers with cost estimation and page-by-page navigation.

## Overview

Side-by-Side Comparison mode lets you parse entire PDF documents with multiple providers simultaneously and compare the results page-by-page. Unlike Battle Mode (single-page, blind testing), this mode gives you complete visibility into how each provider handles your full document.

### Key Features

- **Full Document Parsing**: Parse all pages, not just one
- **Multiple Providers**: Compare up to 3 providers at once
- **Cost Estimation**: See estimated costs before committing
- **Page Navigation**: Jump to any page, review quality throughout document
- **Configuration Control**: Choose models/modes per provider
- **Download Results**: Export markdown for all providers
- **Performance Metrics**: Track processing time and actual costs

### When to Use

**Use Side-by-Side Comparison when**:
- You want to parse a full document
- You need comprehensive quality assessment
- You're evaluating providers for production use
- You want to export results for downstream processing
- Cost transparency matters (see before you spend)

**Use Battle Mode instead when**:
- You want unbiased quality judgment
- Cost minimization is priority (1 page vs full doc)
- Quick comparison needed
- Building intuition about parser quality

## Workflow

### Step 1: Upload PDF

Navigate to http://localhost:3000/parse

**Upload Options**:
- **Drag and drop** PDF onto upload zone
- **Click to browse** files from your system
- **File validation**: Checks file type (must be PDF)

**After Upload**:
- System analyzes document
- Page count returned
- File ID generated for processing

**Supported Documents**:
- Any valid PDF
- No size limit (but consider costs scale with pages)
- Scanned documents work (OCR applied by parsers)
- Multi-column layouts supported
- Complex documents (tables, figures, equations) supported

### Step 2: Select Providers

Choose which providers to compare (1-3):

**Available Providers**:
- ✅ LlamaIndex
- ✅ Reducto
- ✅ LandingAI

**Selection Strategy**:
- **All 3**: Comprehensive comparison, highest cost
- **2 providers**: Balance comparison vs cost
- **1 provider**: Just parse and download (no comparison)

**Recommendation**: Start with 2 providers for your use case, expand to 3 once you know requirements.

### Step 3: Configure Models

For each selected provider, configure parsing options:

#### LlamaIndex Configuration

| Option | Choices | Impact |
|--------|---------|--------|
| Parse Mode | Cost-effective, Agentic, Agentic Plus | Quality vs Cost |
| Model | GPT-4o-mini, Sonnet 4.0 | Speed vs Quality |

**Recommendations**:
- General docs: Cost-effective + GPT-4o-mini
- Complex layouts: Agentic + GPT-4o-mini
- Maximum quality: Agentic Plus + Sonnet 4.0

#### Reducto Configuration

| Option | Choices | Impact |
|--------|---------|--------|
| Mode | Standard, Complex VLM | Cost and figure handling |

**Recommendations**:
- Text-heavy: Standard mode
- Figures/diagrams: Complex VLM mode

#### LandingAI Configuration

| Option | Choices | Impact |
|--------|---------|--------|
| Model | DPT-2 Mini, DPT-2 | Cost vs quality |

**Recommendations**:
- General use: DPT-2 Mini
- Detailed extraction: DPT-2

### Step 4: Review Cost Estimate

Before parsing, system shows estimated total cost:

**Cost Breakdown**:
```
LlamaIndex (Cost-effective):  20 pages × 3 credits × $0.001 = $0.060
Reducto (Standard):           20 pages × 1 credit  × $0.015 = $0.300
LandingAI (DPT-2 Mini):       20 pages × 1.5 credits × $0.01 = $0.300
───────────────────────────────────────────────────────────────
Total Estimated Cost: $0.660
```

**Estimation Accuracy**:
- **Fixed modes**: Exact (LlamaIndex Cost-effective, Reducto modes, LandingAI modes)
- **Agentic modes**: Range (10-90 credits/page depending on complexity)

**Decision Point**: Confirm to proceed or adjust configuration.

### Step 5: Parse Document

Click "Parse" to start full-document parsing.

**What Happens**:
1. Upload file to backend
2. Providers parse in parallel (async)
3. Progress indicators per provider
4. Results stream back as completed

**Duration**:
- **Small docs** (1-10 pages): 30-120 seconds
- **Medium docs** (10-50 pages): 2-10 minutes
- **Large docs** (50+ pages): 10+ minutes

**Progress Indicators**:
- Per-provider status (parsing, complete, error)
- Elapsed time per provider
- Error messages if any fail

**Error Handling**:
- One provider failing doesn't stop others
- Partial results displayed
- Error details shown for debugging

### Step 6: Compare Results

Results displayed side-by-side with synchronized navigation.

**Comparison View**:
```
┌─────────────────┬─────────────────┬─────────────────┐
│  LlamaIndex     │  Reducto        │  LandingAI      │
├─────────────────┼─────────────────┼─────────────────┤
│  Page 1 content │  Page 1 content │  Page 1 content │
│  (markdown)     │  (markdown)     │  (markdown)     │
└─────────────────┴─────────────────┴─────────────────┘
         [<] [Page 1 / 20] [>]
```

**Navigation**:
- **Arrow buttons**: Previous/Next page
- **Page input**: Jump to specific page
- **Keyboard shortcuts**: Arrow keys (left/right)

**Synchronized Scrolling**:
- Scroll one panel, others follow
- Maintains relative position
- Helps compare aligned content

**View Options**:
- Toggle PDF preview (if available)
- Expand/collapse panels
- Adjust panel widths

### Step 7: Analyze Quality

Evaluate parsing quality across providers:

**Quality Dimensions**:

1. **Text Accuracy**
   - Is text correctly recognized?
   - Any OCR errors or hallucinations?
   - Proper character encoding?

2. **Structure Preservation**
   - Headings correctly identified?
   - Lists properly formatted?
   - Paragraph breaks maintained?

3. **Table Handling**
   - Tables detected and extracted?
   - Column alignment preserved?
   - Cell contents accurate?
   - Markdown table formatting clean?

4. **Figure Handling**
   - Captions extracted?
   - Context maintained?
   - Figures summarized (if applicable)?

5. **Equation Handling**
   - Math expressions recognized?
   - LaTeX or text representation?
   - Accuracy of notation?

6. **Markdown Quality**
   - Clean, readable markdown?
   - Proper syntax?
   - Minimal artifacts?

**Comparison Strategies**:
- **Spot check**: Sample 5-10 representative pages
- **Problematic pages**: Check complex pages (tables, figures)
- **Consistency**: Does quality hold across document?
- **Edge cases**: Headers, footers, multi-column sections

### Step 8: Review Costs

Actual costs displayed after parsing completes.

**Cost Display**:
```
Provider        | Pages | Credits | USD/Credit | Total Cost
─────────────────────────────────────────────────────────
LlamaIndex      |  20   |  60     | $0.001     | $0.060
Reducto         |  20   |  20     | $0.015     | $0.300
LandingAI       |  20   |  30     | $0.010     | $0.300
─────────────────────────────────────────────────────────
Total Actual: $0.660  (Estimated: $0.660)
```

**Cost Analysis**:
- Compare actual vs estimated
- Identify most cost-effective provider
- Calculate cost per page
- Evaluate quality vs cost tradeoff

**Variance**:
- Fixed modes: Actual = Estimated
- Agentic modes: Actual may vary (10-90 credit range)

### Step 9: Download Results

Export markdown results for downstream use.

**Download Options**:
- **Per provider**: Download LlamaIndex results only
- **All providers**: Zip file with all markdowns
- **With metadata**: Include costs, timing, configs

**File Formats**:
- `.md` - Clean markdown
- `.json` - Structured data with metadata
- `.zip` - Bundle of all files

**Use Cases**:
- Feed to RAG system
- Further processing/analysis
- Archival/documentation
- Comparison with future versions

## Advanced Features

### Batch Processing

Process multiple documents sequentially:

1. Parse document 1 → Download results
2. Upload document 2 → Use same configs
3. Repeat for corpus

**Tip**: API keys and configs persist in localStorage, fast batch workflow.

### Cost Optimization

Find the cheapest acceptable quality:

**Strategy**:
1. Parse with all providers (baseline)
2. Identify acceptable quality threshold
3. Re-parse with cheaper modes
4. Compare quality degradation vs cost savings

**Example**:
- Baseline: All @ highest quality = $1.50
- Test: All @ cheapest = $0.30 (80% savings)
- Evaluate: Is quality acceptable?
- Decision: Use cheap for 90% of docs, expensive for critical 10%

### Provider Selection

Choose optimal provider for your document type:

**Document Profiling**:
- Mostly text? → LlamaIndex Cost-effective
- Heavy tables? → Reducto or LandingAI
- Lots of figures? → Reducto Complex VLM
- Mixed content? → Compare all

**Build a Matrix**:
| Doc Type | Best Provider | Mode | Cost/Page |
|----------|---------------|------|-----------|
| Research papers | LlamaIndex | Cost-effective | $0.003 |
| Financial reports | Reducto | Standard | $0.015 |
| Technical manuals | LandingAI | DPT-2 | $0.030 |

### Quality Tracking

Track quality metrics over time:

1. Parse test set with all providers
2. Score results (accuracy, completeness, formatting)
3. Repeat monthly
4. Track provider improvements
5. Adjust choices based on trends

## Performance Tips

### Faster Parsing

- **Fewer providers**: Parse with 1-2 instead of 3
- **Cheaper modes**: Cost-effective modes often faster
- **Smaller documents**: Split large PDFs if possible

### Lower Costs

- **Sample first**: Parse first 5-10 pages to evaluate
- **Selective parsing**: Only pages with important content
- **Cost-effective defaults**: Start cheap, upgrade if needed

### Better Quality

- **Agentic modes**: For complex documents worth the cost
- **Multiple providers**: Cross-validate results
- **Manual review**: Spot-check critical pages

## Troubleshooting

### Parsing Fails

**Issue**: One or more providers fail to parse

**Solutions**:
- Check API key validity
- Verify API credits/quota
- Review backend logs for errors
- Try smaller page range
- Try different document

### Results Look Bad

**Issue**: All providers produce poor results

**Possible Causes**:
- Document is image-only scan (OCR limitations)
- PDF is corrupted or malformed
- Extremely complex layout
- Non-standard encoding

**Solutions**:
- Try different parsers
- Use Agentic or VLM-enhanced modes
- Pre-process PDF (clean scan, re-PDF)
- Manual review if quality critical

### Cost Higher Than Expected

**Issue**: Actual cost exceeds estimate

**Explanation**:
- Agentic modes use variable credits (10-90 range)
- Complex pages trigger higher usage
- Estimate shows range or average

**Prevention**:
- Use fixed-cost modes for predictability
- Test with small sample first
- Monitor per-page costs during parsing

### Download Fails

**Issue**: Cannot download results

**Solutions**:
- Check browser console for errors
- Verify backend still has files (temporary storage)
- Try downloading single provider vs all
- Re-parse if files expired

## API Reference

Side-by-side parsing endpoints:

### Parse Full Document

```http
POST /api/v1/parsing/compare
Content-Type: application/json

{
  "file_id": "uuid-string",
  "providers": ["llamaindex", "reducto", "landingai"],
  "api_keys": {
    "llamaindex": "llx-...",
    "reducto": "red-...",
    "landingai": "va-..."
  },
  "configs": {
    "llamaindex": {
      "parse_mode": "parse_page_with_llm",
      "model": "openai-gpt-4-1-mini"
    },
    "reducto": {
      "mode": "standard",
      "summarize_figures": false
    },
    "landingai": {
      "model": "dpt-2-latest"
    }
  }
}
```

**Response**:
```json
{
  "results": {
    "llamaindex": {
      "pages": [
        { "page_number": 1, "markdown": "...", "images": [] },
        { "page_number": 2, "markdown": "...", "images": [] }
      ],
      "total_pages": 20,
      "processing_time": 45.3,
      "cost": 0.060
    },
    "reducto": { /* ... */ },
    "landingai": { /* ... */ }
  }
}
```

### Download Results

```http
GET /api/v1/parsing/download-result/{file_id}/{provider}
```

Returns markdown file.

## Related Documentation

- **[Battle Mode](BATTLE_MODE.md)** - Blind A/B testing alternative
- **[Parsing Providers](PARSING_PROVIDERS.md)** - Provider specifications
- **[Pricing Guide](PRICING.md)** - Cost calculator and optimization
- **[Quick Start](QUICK_START.md)** - Get started in 5 minutes
