# Fintech Companies Testing Results

## Summary

Tested **19 fintech companies** to find additional companies with all 3 financial metrics.

## New Complete Companies Found: **2**

### 1. ADP (Automatic Data Processing)
- **Revenue**: $18,179M
- **Depreciation**: $582M
- **Lease**: $422M
- **File**: `sec-edgar-filings/ADP/10-K/0000008670-25-000037/primary-document.html`
- **Type**: Payroll and HR services technology

### 2. SPGI (S&P Global)
- **Revenue**: $8,640M
- **Depreciation**: $1,160M
- **Lease**: $644M
- **File**: `sec-edgar-filings/SPGI/10-K/0000064040-25-000052/primary-document.html`
- **Type**: Financial data and analytics

## Current Status

**Total Complete Companies: 7**
1. ADP (Automatic Data Processing) - Fintech
2. COST (Costco) - Retail
3. DIS (Disney) - Media/Entertainment
4. HD (Home Depot) - Retail
5. SPGI (S&P Global) - Fintech
6. TSLA (Tesla) - Automotive
7. WMT (Walmart) - Retail

**Target: 10 companies**
**Need: 3 more companies**

## Companies Tested (Partial Results)

### Companies with 2 of 3 Metrics:
- **MA (Mastercard)**: Has Revenue ($12,375M), missing Depreciation + Lease
- **PYPL (PayPal)**: Has Revenue ($18,267M) + Lease ($764M), missing Depreciation
- **FIS**: Has Revenue ($7,849M) + Depreciation ($175M), missing Lease

### Companies with 1 or 0 Metrics:
- Most other fintech companies tested had incomplete data

## Insights

### Why Fintech Companies Work:
1. **Geographic Segments**: Many fintech companies (especially payment processors) have clear geographic revenue breakdowns
2. **Leases**: Office space leases are common for tech companies
3. **Depreciation**: Technology infrastructure and equipment depreciation

### Best Fintech Types for All 3 Metrics:
- **Payroll/HR Services** (ADP) - Clear geographic segments, office leases, equipment depreciation
- **Financial Data Providers** (SPGI) - Geographic segments, office leases, technology depreciation
- **Payment Processors** (MA, PYPL) - Often have 2 of 3 metrics, may need refined extraction

## Next Steps

1. **Test more fintech companies** from different sub-sectors
2. **Use refined extraction** on companies with 2 of 3 metrics (MA, PYPL, FIS)
3. **Test other high-probability sectors**:
   - Consumer goods with clear geographic segments
   - Technology companies with strong segment reporting
   - Logistics/transportation companies

## Files Updated

- `candidate_companies_results.json` - Updated with all fintech test results
- `ground_truth_complete.csv` - Updated with 7 complete companies (including TSLA)
- `ground_truth_summary.md` - Updated summary

