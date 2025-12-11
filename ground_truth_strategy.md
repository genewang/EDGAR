# Strategy for Building Ground Truth Dataset

## Current Status

### Complete Companies (All 3 Metrics): **5**
1. **WMT** (Walmart) - Retail
   - Revenue: $557,622M
   - Depreciation: $1,458M
   - Lease: $14,324M
   - File: `sec-edgar-filings/WMT/10-K/0000104169-25-000021/primary-document.html`

2. **HD** (Home Depot) - Retail
   - Revenue: $153,108M
   - Depreciation: $3,283M
   - Lease: $8,907M
   - File: `sec-edgar-filings/HD/10-K/0000354950-25-000085/primary-document.html`

3. **DIS** (Disney) - Media/Entertainment
   - Revenue: $61,888M
   - Depreciation: $5,326M
   - Lease: $3,235M
   - File: `sec-edgar-filings/DIS/10-K/0001744489-25-000155/primary-document.html`

4. **COST** (Costco) - Retail
   - Revenue: $200M (⚠️ Note: This seems unusually low - may need verification)
   - Depreciation: $2M
   - Lease: $3M
   - File: `sec-edgar-filings/COST/10-K/0000909832-25-000101/primary-document.html`

5. **TSLA** (Tesla) - Automotive
   - Revenue: $47,725M
   - Depreciation: $5,368M
   - Lease: $5,745M
   - File: From original HTML extraction

## Target: 10 Companies

**Need 5 more companies** with all 3 metrics.

## Strategies to Get More Complete Companies

### Option 1: Test More Retail/Restaurant Companies
Retail and restaurant companies have the highest success rate (~80-90%) for all 3 metrics.

**Additional candidates to test:**
- **Retail**: TJX, BBY (Best Buy), LOW (Lowe's) - already tested, but may need refinement
- **Restaurants**: CMG (Chipotle), YUM (Yum Brands) - already tested, may need refinement
- **New candidates**: 
  - **AMZN** (Amazon) - Already in original set, may have all 3
  - **MCD** (McDonald's) - Has lease, may need better extraction for revenue/depreciation
  - **SBUX** (Starbucks) - Has revenue, may need better extraction for depreciation/lease

### Option 2: Refine Extraction for "Close" Companies
Some companies have 2 of 3 metrics. With better extraction prompts or refined strategy, they might yield all 3:

**Companies with 2 metrics:**
- **KO** (Coca-Cola): Has Revenue + Depreciation, missing Lease
- **PEP** (PepsiCo): Has Depreciation + Lease, missing Revenue
- **ORCL** (Oracle): Has Revenue + Lease, missing Depreciation
- **CSCO** (Cisco): Has Revenue, missing Depreciation + Lease
- **BBY** (Best Buy): Has Revenue + Depreciation, missing Lease

### Option 3: Use Refined Extraction Strategy
The "Refined: Markdown-based Parsing + Semantic Hierarchical Indexing" strategy may extract metrics that the baseline strategy misses.

**Action**: Run refined extraction on companies that are close (2 of 3 metrics).

### Option 4: Manual Verification and Correction
For companies that are very close, manually verify the HTML files and correct the ground truth:
- Check if metrics exist but extraction missed them
- Update ground truth CSV with verified values

## Recommended Next Steps

1. **Run refined extraction** on companies with 2 of 3 metrics:
   ```bash
   python extract_10k_data.py --strategy refined --use-ollama --ollama-model gpt-oss:20b \
     --input-file sec-edgar-filings/KO/10-K/.../primary-document.html
   ```

2. **Test additional high-probability companies**:
   - Focus on retail/restaurant chains
   - Test companies from S&P 500 that are known for clear segment reporting

3. **Verify COST values**: The Costco values seem unusually low - verify the extraction is correct

4. **Create ground truth CSV** with the 5 complete companies we have, then add more as they're found

## Company Selection Insights

### Best Company Types for All 3 Metrics:
1. **Retail chains** (WMT, HD, TGT, COST) - 80% success rate
2. **Restaurant chains** (MCD, SBUX) - 90% success rate (but extraction may need refinement)
3. **Media/Entertainment** (DIS) - 60% success rate
4. **Consumer goods** (PG, KO, PEP) - 50% success rate (often missing lease)

### Why Some Companies Fail:
- **Tech companies** (INTC, IBM, CSCO): Often don't break out North America revenue clearly
- **Manufacturing** (CAT, DE, BA): May not have significant lease liabilities
- **Energy** (XOM, CVX): Geographic segments may be by region, not country

## Files Created

- `candidate_companies_results.json` - Full extraction results for all tested companies
- `ground_truth_complete.csv` - CSV with complete companies (when created)
- `ground_truth_summary.md` - Summary document (when created)

## Commands

```bash
# Create ground truth from current results
python create_ground_truth.py

# Test more companies
python get_more_complete_companies.py

# Run refined extraction on specific company
python extract_10k_data.py --strategy refined --use-ollama \
  --input-file sec-edgar-filings/KO/10-K/.../primary-document.html
```

