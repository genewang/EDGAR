# Feature Change Summary

## Changes Made

The extraction system has been updated to extract **three new features** instead of the previous ones:

### Old Features (Removed):
- North America Revenue
- Depreciation & Amortization  
- Lease Liabilities

### New Features (Current):
1. **CIK (Central Index Key)** - Company identifier from SEC filings
2. **Total Revenue** - From Income Statement (in millions USD)
3. **Net Income** - From Income Statement (in millions USD)

## Updated Files

1. **`extract_10k_data.py`**:
   - Updated `FinancialMetrics` class with new fields
   - Updated extraction queries for baseline and refined methods
   - Updated evaluator to handle CIK (string comparison) and numeric fields
   - CIK validation includes padding to 10 digits

2. **`ground_truth_complete.csv`**:
   - Updated column structure: `ticker, cik, total_revenue, net_income, html_file, fiscal_year`
   - CIK values automatically extracted from HTML file paths
   - **Note**: `total_revenue` and `net_income` columns are empty and need to be filled

## Next Steps

### 1. Populate Ground Truth Values

You need to manually fill in `total_revenue` and `net_income` for each company in `ground_truth_complete.csv`. These values should be:
- In **millions of USD**
- From the **most recent fiscal year** in the 10-K filing
- From the **Income Statement** (Statement of Operations)

### 2. Run Extraction

Once ground truth is populated, run extraction on all 10 companies:

```bash
python extract_10k_data.py --mode both --pdf-dir pdfs --ground-truth ground_truth_complete.csv --evaluate --output extraction_results_new_features.json --use-ollama
```

### 3. Expected Results

The extraction will now:
- Extract CIK from the filing header/cover page
- Extract Total Revenue from Income Statement
- Extract Net Income from Income Statement
- Compare against ground truth with:
  - CIK: Exact string match
  - Total Revenue & Net Income: Within 1% tolerance

## Current Ground Truth Status

- ✅ CIK: All 10 companies have CIK values extracted
- ⚠️ Total Revenue: Empty - needs manual entry
- ⚠️ Net Income: Empty - needs manual entry

## Example Ground Truth Entry

```csv
ticker,cik,total_revenue,net_income,html_file,fiscal_year
AAPL,0000320193,383285.0,96995.0,sec-edgar-filings/AAPL/10-K/...,2023.0
```

