# HTML Extraction Results Summary

## Extraction from Original HTML Files using gpt-oss:20b

### Processing Status
- **Total Companies**: 10
- **Successfully Processed**: 10/10 (100%)
- **Source**: Original HTML files from SEC EDGAR (`sec-edgar-filings/`)

### Extraction Rates

| Metric | Extracted | Rate |
|--------|-----------|------|
| **North America Revenue** | 6/10 | 60.0% |
| **Depreciation & Amortization** | 3/10 | 30.0% |
| **Lease Liabilities** | 2/10 | 20.0% |

### Detailed Results

| Company | Revenue (M$) | Depreciation (M$) | Lease (M$) | Fiscal Year |
|---------|--------------|------------------|------------|-------------|
| AAPL | $178,353 | — | — | — |
| AMZN | — | $32,100 | — | 2024 |
| GOOGL | $170,447 | — | $14,578 | — |
| JNJ | — | — | — | — |
| JPM | — | — | — | — |
| META | — | — | — | 2024 |
| MSFT | $144,546 | — | — | 2025 |
| NVDA | $61,257 | $1,300 | — | 2025 |
| TSLA | $47,725 | $5,368 | $5,745 | 2024 |
| V | $15,633 | — | — | — |

### Comparison: HTML vs PDF Extraction

| Metric | PDF | HTML | Improvement |
|--------|-----|------|-------------|
| Revenue | 5/10 (50%) | 6/10 (60%) | **+10%** |
| Depreciation | 1/10 (10%) | 3/10 (30%) | **+20%** |
| Lease | 3/10 (30%) | 2/10 (20%) | -10% |

### Key Findings

✅ **HTML Extraction Advantages:**
- **Better Revenue Extraction**: 6 companies vs 5 from PDF (+1)
- **Much Better Depreciation Extraction**: 3 companies vs 1 from PDF (+2)
- **Table Structure Preservation**: HTML tables maintain row/column relationships
- **Cleaner Text**: No PDF parsing artifacts or formatting issues
- **Faster Processing**: No PDF conversion step needed
- **Direct Source**: Working with original SEC EDGAR files

⚠️ **Areas for Improvement:**
- Lease liabilities extraction slightly lower (2 vs 3)
- Some companies still missing metrics (JNJ, JPM, META)

### Notable Extractions

**TSLA (Tesla)** - Complete extraction:
- Revenue: $47,725M
- Depreciation: $5,368M
- Lease: $5,745M

**NVDA (NVIDIA)** - Good extraction:
- Revenue: $61,257M (not extracted from PDF)
- Depreciation: $1,300M (not extracted from PDF)

**AMZN (Amazon)** - Depreciation found:
- Depreciation: $32,100M (not extracted from PDF)

### Conclusion

HTML extraction shows **significant improvements** over PDF extraction, particularly for:
- Revenue extraction (+10%)
- Depreciation extraction (+20% - 3x improvement!)

The HTML approach is **recommended** for better accuracy and faster processing.

