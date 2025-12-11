# 10-K Report Data Extraction and Evaluation System

This system extracts complex financial metrics from 10-K PDF filings using two approaches:
1. **Baseline**: Naive text chunking (expected <60% accuracy on tables)
2. **Refined**: LlamaParse Markdown parsing (target >90% accuracy)

## Overview

The system extracts three challenging metrics that require table understanding:
- **North America Revenue**: From Segment Information tables
- **Depreciation & Amortization**: From Cash Flow Statement
- **Total Lease Liabilities**: From Balance Sheet (sum of current + non-current)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

#### Option A: Using OpenAI (Default)

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Then edit `.env` and add your API keys:
- `OPENAI_API_KEY`: Required for both baseline and refined extraction
- `LLAMA_CLOUD_API_KEY`: Required for refined extraction (get from https://cloud.llamaindex.ai/)

#### Option B: Using Local Ollama Server

To temporarily switch to a local Ollama server:

1. **Install Ollama support**:
   ```bash
   pip install llama-index-llms-ollama
   ```

2. **Start Ollama server** and pull the model:
   ```bash
   ollama serve
   ollama pull gpt-oss:20b
   ```

3. **Use the `--use-ollama` flag** when running extraction:
   ```bash
   python extract_10k_data.py --mode both --use-ollama --pdf-dir pdfs
   ```

   Or set environment variable:
   ```bash
   export USE_OLLAMA=true
   python extract_10k_data.py --mode both --pdf-dir pdfs
   ```

**Configuration Options:**
- `--use-ollama`: Use local Ollama server instead of OpenAI
- `--ollama-model MODEL`: Specify Ollama model (default: `gpt-oss:20b`)
- `--ollama-base-url URL`: Specify Ollama server URL (default: `http://localhost:11434`)
- Environment variables: `USE_OLLAMA`, `OLLAMA_MODEL`, `OLLAMA_BASE_URL`

**Note:** When using Ollama, you may still need `OPENAI_API_KEY` for embeddings if Ollama embeddings are unavailable.

### 3. Prepare Ground Truth Data

Edit `ground_truth.csv` with manually verified values from the PDFs:

```csv
ticker,north_america_revenue,depreciation_amortization,lease_liabilities
AAPL,167814.0,11104.0,11129.0
MSFT,123456.0,9876.0,5432.0
...
```

Values should be in **millions of USD**.

## Usage

### Extract Metrics (Both Methods)

```bash
python extract_10k_data.py --mode both --pdf-dir pdfs --evaluate
```

### Extract with Baseline Only

```bash
python extract_10k_data.py --mode baseline --pdf-dir pdfs
```

### Extract with Refined Only

**With OpenAI:**
```bash
python extract_10k_data.py --mode refined --pdf-dir pdfs
```

**With Ollama:**
```bash
python extract_10k_data.py --mode refined --pdf-dir pdfs --use-ollama
```

### Extract Without Evaluation

```bash
python extract_10k_data.py --mode both --pdf-dir pdfs
```

## Output Files

- `extraction_results.json`: Raw extraction results from both methods
- `evaluation_extraction_results.json`: Evaluation against ground truth (if `--evaluate` flag used)

## How It Works

### Baseline Approach

1. Extracts raw text from PDF using PyPDF
2. Chunks text into 1024-token blocks
3. Creates vector index
4. Queries LLM with context chunks
5. **Limitation**: Loses table structure, leading to column confusion

### Refined Approach

1. Parses PDF to Markdown using LlamaParse (preserves table structure!)
2. Filters for relevant sections (Item 7, Item 8)
3. Creates vector index from Markdown documents
4. Queries LLM with table-aware context
5. **Advantage**: Maintains row-column relationships

## Evaluation

The evaluation framework compares extracted values against ground truth with:
- **Exact Match**: Within 1% tolerance (accounts for rounding)
- **Error Classification**:
  - None: Within tolerance
  - Minor: Rounding/formatting errors (1-10% error)
  - Moderate: Partial match (10-50% error)
  - Major: Wrong value/column (>50% error)

## Expected Results

- **Baseline**: ~40-60% accuracy (struggles with tables)
- **Refined**: ~85-95% accuracy (table-aware parsing)

## Troubleshooting

### "LlamaParse not available"
- Install: `pip install llama-parse`
- Get API key from https://cloud.llamaindex.ai/

### "OPENAI_API_KEY not found"
- Create `.env` file with your OpenAI API key
- Or export: `export OPENAI_API_KEY=your_key`
- Or use `--use-ollama` flag to use local Ollama server instead

### "Ollama support requested but llama-index-llms-ollama is not installed"
- Install: `pip install llama-index-llms-ollama`
- Make sure Ollama server is running: `ollama serve`
- Verify model is available: `ollama list`
- Check Ollama server URL matches (default: `http://localhost:11434`)

### Low Accuracy
- Check ground truth values are correct
- Verify PDFs are readable (not corrupted)
- Try refined approach if using baseline

## Next Steps

1. **Populate Ground Truth**: Manually extract values from PDFs into `ground_truth.csv`
2. **Run Extraction**: Execute with `--evaluate` flag
3. **Analyze Errors**: Review evaluation results to identify patterns
4. **Iterate**: Refine prompts or add post-processing based on error analysis

