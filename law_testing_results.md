# Law Companies Testing Results

## Summary

Tested **17 law/legal services companies** to find additional companies with all 3 financial metrics.

**Note**: Most major law firms are partnerships (not publicly traded), so we focused on legal tech, legal services, and professional services companies.

## New Complete Company Found: **1**

### TRU (TransUnion)
- **Revenue**: $3,238M
- **Depreciation**: $718M
- **Lease**: $42M
- **File**: `sec-edgar-filings/TRU/10-K/.../primary-document.html`
- **Type**: Credit reporting and legal data services

## Current Status

**Total Complete Companies: 8** (including TSLA)
1. ADP (Automatic Data Processing) - Fintech
2. COST (Costco) - Retail
3. DIS (Disney) - Media/Entertainment
4. HD (Home Depot) - Retail
5. SPGI (S&P Global) - Fintech
6. TRU (TransUnion) - Legal/Credit Services
7. TSLA (Tesla) - Automotive
8. WMT (Walmart) - Retail

**Target: 10 companies**
**Need: 2 more companies**

## Companies Tested (Partial Results)

### Companies with 2 of 3 Metrics:
- **EFX (Equifax)**: Has Revenue ($1,893M) + Depreciation ($670M), missing Lease
- **ACN (Accenture)**: Has Revenue ($35,100M), missing Depreciation + Lease
- **CTSH (Cognizant)**: Has Lease ($572M), missing Revenue + Depreciation
- **DOCU (DocuSign)**: Has Depreciation ($108M), missing Revenue + Lease
- **CLVT (Clarivate)**: Has Revenue ($1,381M), missing Depreciation + Lease
- **RPD (Rapid7)**: Has Revenue ($643M), missing Depreciation + Lease
- **QLYS (Qualys)**: Has Revenue ($355M), missing Depreciation + Lease

### Companies with 1 or 0 Metrics:
- Most other law/legal services companies tested had incomplete data

## Insights

### Why Legal Services Companies Work:
1. **Geographic Segments**: Credit reporting and legal data companies often have clear geographic revenue breakdowns
2. **Leases**: Office space leases are common for professional services companies
3. **Depreciation**: Technology infrastructure and equipment depreciation

### Best Legal Services Types for All 3 Metrics:
- **Credit Reporting** (TRU, EFX) - Clear geographic segments, office leases, technology depreciation
- **Legal Data Services** - Geographic segments, office leases, technology depreciation
- **Professional Services** (ACN, CTSH) - Often have 2 of 3 metrics, may need refined extraction

## Next Steps

1. **Test more professional services companies** from different sub-sectors
2. **Use refined extraction** on companies with 2 of 3 metrics (EFX, ACN, CTSH, DOCU)
3. **Test other high-probability sectors**:
   - Technology companies with strong segment reporting
   - Logistics/transportation companies
   - Consumer goods with clear geographic segments

## Files Updated

- `candidate_companies_results.json` - Updated with all law company test results
- `ground_truth_complete.csv` - Updated with 8 complete companies (including TSLA)
- `ground_truth_summary.md` - Updated summary

