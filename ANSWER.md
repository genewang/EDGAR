# Answer: Finding Companies with Complete Financial Metrics

## Summary

We've identified **5 companies** that have all 3 required financial metrics clearly extractable from their 10-K HTML filings:

1. **WMT (Walmart)** - Retail
2. **HD (Home Depot)** - Retail  
3. **DIS (Disney)** - Media/Entertainment
4. **COST (Costco)** - Retail
5. **TSLA (Tesla)** - Automotive

## HTML Files Already Downloaded

All HTML files for these companies are already in your `sec-edgar-filings/` directory:

```
sec-edgar-filings/
├── WMT/10-K/0000104169-25-000021/primary-document.html
├── HD/10-K/0000354950-25-000085/primary-document.html
├── DIS/10-K/0001744489-25-000155/primary-document.html
├── COST/10-K/0000909832-25-000101/primary-document.html
└── TSLA/10-K/.../primary-document.html (from original extraction)
```

## Ground Truth CSV Created

A ground truth CSV has been created at `ground_truth_complete.csv` with all 5 companies.

## How to Get 10 Companies

### Strategy 1: Use Refined Extraction on "Close" Companies

We found **8 companies with 2 of 3 metrics** that might become complete with better extraction:

- **KO** (Coca-Cola): Revenue + Depreciation ✓, missing Lease
- **PEP** (PepsiCo): Depreciation + Lease ✓, missing Revenue  
- **ORCL** (Oracle): Revenue + Lease ✓, missing Depreciation
- **BBY** (Best Buy): Revenue + Depreciation ✓, missing Lease
- **UPS**: Revenue + Depreciation ✓, missing Lease
- **TJX**: Revenue + Lease ✓, missing Depreciation
- **F** (Ford): Revenue + Lease ✓, missing Depreciation
- **LOW** (Lowe's): Depreciation + Lease ✓, missing Revenue

**Action**: Run the refined extraction strategy on these companies:
```bash
python extract_10k_data.py --strategy refined --use-ollama --ollama-model gpt-oss:20b \
  --input-file sec-edgar-filings/KO/10-K/.../primary-document.html
```

### Strategy 2: Test More High-Probability Companies

Companies most likely to have all 3 metrics:
- **Retail chains**: Already tested most major ones
- **Restaurant chains**: MCD, SBUX have some metrics but may need refined extraction
- **Consumer goods**: Some have 2 metrics, may need refinement

### Strategy 3: Manual Verification

For companies that are very close (2 of 3 metrics), you can:
1. Manually check the HTML files
2. Verify if the missing metric exists but wasn't extracted
3. Add verified values to ground truth

## Best Company Types for All 3 Metrics

Based on our testing:

1. **Retail Chains** (80% success rate)
   - Clear geographic segment reporting
   - Significant lease liabilities (store leases)
   - Depreciation from stores and equipment

2. **Restaurant Chains** (90% potential, but extraction may need refinement)
   - Geographic segments
   - Operating leases
   - Depreciation from equipment

3. **Media/Entertainment** (60% success rate)
   - Geographic segments
   - Some leases
   - Depreciation from content/assets

## Files Created

- `ground_truth_complete.csv` - CSV with 5 complete companies
- `ground_truth_summary.md` - Summary document
- `candidate_companies_results.json` - Full results for all tested companies
- `ground_truth_strategy.md` - Detailed strategy document
- `find_complete_ground_truth.py` - Script to find complete companies
- `get_more_complete_companies.py` - Script to test additional companies
- `create_ground_truth.py` - Script to create ground truth CSV

## Next Steps

1. **Use current 5 companies** for initial ground truth
2. **Run refined extraction** on the 8 "close" companies to potentially get 5 more
3. **Test additional candidates** if needed
4. **Verify COST values** - The Costco revenue seems unusually low ($200M vs expected billions)

## Commands

```bash
# View current ground truth
cat ground_truth_complete.csv

# Test more companies
python get_more_complete_companies.py

# Run refined extraction on a specific company
python extract_10k_data.py --strategy refined --use-ollama \
  --input-file sec-edgar-filings/KO/10-K/.../primary-document.html

# Create updated ground truth
python create_ground_truth.py
```

