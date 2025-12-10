# 10-K Extraction System - Project Summary

## What Was Built

A comprehensive system for extracting financial metrics from 10-K PDF filings with two extraction approaches and evaluation framework.

## Files Created

### Core Extraction System
- **`extract_10k_data.py`**: Main extraction script with:
  - Baseline extractor (naive text chunking)
  - Refined extractor (LlamaParse Markdown parsing)
  - Evaluation framework
  - Command-line interface

### Data Files
- **`ground_truth.csv`**: Template for manually verified values
- **`populate_ground_truth.py`**: Interactive helper to populate ground truth

### Documentation
- **`EXTRACTION_README.md`**: Comprehensive documentation
- **`QUICKSTART.md`**: Step-by-step getting started guide
- **`PROJECT_SUMMARY.md`**: This file

### Configuration
- **`requirements.txt`**: Updated with all dependencies
- **`.env.example`**: Template for API keys (create `.env` from this)

## System Architecture

```
PDF Files → Parser → Vector Index → LLM Query → Structured Output → Evaluation
```

### Baseline Flow
1. PyPDF extracts raw text
2. Text chunked into 1024-token blocks
3. Vector index created
4. LLM queries with context chunks
5. **Limitation**: Loses table structure

### Refined Flow
1. LlamaParse converts PDF to Markdown (preserves tables!)
2. Documents filtered for Item 7/8
3. Vector index created from Markdown
4. LLM queries with table-aware context
5. **Advantage**: Maintains row-column relationships

## Metrics Extracted

1. **North America Revenue**: From Segment Information tables
2. **Depreciation & Amortization**: From Cash Flow Statement
3. **Total Lease Liabilities**: From Balance Sheet

## Expected Performance

- **Baseline**: 40-60% accuracy (struggles with table structure)
- **Refined**: 85-95% accuracy (table-aware parsing)

## Next Steps

### 1. Set Up Environment
```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
```

### 2. Populate Ground Truth
- Open each PDF in `pdfs/` directory
- Extract the 3 metrics manually
- Enter values in `ground_truth.csv` or use `populate_ground_truth.py`

### 3. Run Extraction
```bash
python extract_10k_data.py --mode both --pdf-dir pdfs --evaluate
```

### 4. Analyze Results
- Review `extraction_results.json` for raw outputs
- Check `evaluation_extraction_results.json` for accuracy metrics
- Identify error patterns and iterate

## Key Features

✅ **Dual Approach**: Compare baseline vs refined methods
✅ **Structured Output**: Pydantic models ensure type safety
✅ **Evaluation Framework**: Automatic comparison with ground truth
✅ **Error Classification**: Categorizes errors (retrieval, reasoning, formatting)
✅ **Table-Aware**: Refined method preserves table structure via Markdown

## Technical Stack

- **Python 3.11+**: Core language
- **LlamaIndex**: Orchestration and indexing
- **LlamaParse**: Advanced PDF parsing (Markdown output)
- **OpenAI GPT-4o**: LLM for extraction
- **Pydantic**: Structured data validation
- **Pandas**: Data manipulation and evaluation

## API Keys Required

1. **OpenAI API Key** (Required)
   - Get from: https://platform.openai.com/api-keys
   - Used for: Both baseline and refined extraction

2. **LlamaCloud API Key** (Required for refined method)
   - Get from: https://cloud.llamaindex.ai/
   - Free tier available
   - Used for: LlamaParse PDF to Markdown conversion

## File Structure

```
EDGAR/
├── pdfs/                          # 10-K PDF files (10 files)
├── extract_10k_data.py            # Main extraction script
├── populate_ground_truth.py       # Ground truth helper
├── ground_truth.csv               # Manual verification data
├── requirements.txt               # Dependencies
├── .env                          # API keys (create from .env.example)
├── EXTRACTION_README.md           # Full documentation
├── QUICKSTART.md                  # Quick start guide
└── PROJECT_SUMMARY.md             # This file
```

## Usage Examples

### Extract with baseline only
```bash
python extract_10k_data.py --mode baseline --pdf-dir pdfs
```

### Extract with refined only
```bash
python extract_10k_data.py --mode refined --pdf-dir pdfs
```

### Extract both and evaluate
```bash
python extract_10k_data.py --mode both --pdf-dir pdfs --evaluate
```

### Extract without evaluation
```bash
python extract_10k_data.py --mode both --pdf-dir pdfs
```

## Output Files

- **`extraction_results.json`**: Raw extraction results from both methods
- **`evaluation_extraction_results.json`**: Evaluation metrics (if `--evaluate` used)

## Evaluation Metrics

- **Exact Match**: Within 1% tolerance (accounts for rounding)
- **Error Types**:
  - None: Within tolerance
  - Minor: Rounding/formatting (1-10% error)
  - Moderate: Partial match (10-50% error)
  - Major: Wrong value/column (>50% error)

## Support

For issues or questions:
1. Check `EXTRACTION_README.md` for detailed documentation
2. Review `QUICKSTART.md` for setup help
3. Check error messages for specific guidance

