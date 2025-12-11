# Strategy for Finding Companies with Complete Financial Metrics

## Target Metrics
1. **North America Revenue** - From Segment Information/Geographic Revenue tables
2. **Depreciation & Amortization** - From Cash Flow Statement
3. **Lease Liabilities** - From Balance Sheet (current + non-current)

## Company Selection Criteria

### Companies Likely to Have All 3 Metrics

#### 1. **Retail Companies** (High probability)
- **Why**: Clear geographic segments, significant lease liabilities (store leases)
- **Examples**: WMT, TGT, COST, HD
- **Expected**: All 3 metrics clearly reported

#### 2. **Restaurant Chains** (High probability)
- **Why**: Geographic segments, significant operating leases
- **Examples**: MCD, SBUX, CMG
- **Expected**: All 3 metrics clearly reported

#### 3. **Consumer Goods** (Medium-High probability)
- **Why**: Geographic segments, some depreciation, some leases
- **Examples**: PG, KO, PEP, NKE
- **Expected**: Revenue + Depreciation (lease may vary)

#### 4. **Manufacturing** (Medium probability)
- **Why**: Geographic segments, high depreciation, some leases
- **Examples**: CAT, DE, BA
- **Expected**: Revenue + Depreciation (lease may vary)

#### 5. **Tech with Manufacturing** (Medium probability)
- **Why**: Geographic segments, depreciation from facilities
- **Examples**: INTC, ORCL, CSCO
- **Expected**: Revenue + Depreciation

## Current Status

### Already Tested (from HTML extraction)
- **TSLA**: ✓ All 3 metrics extracted
- **NVDA**: Revenue + Depreciation (missing lease)
- **MSFT**: Revenue + Depreciation + Lease (from PDF)

### Best Candidates for Complete Data

1. **WMT (Walmart)** - Retail, clear segments, leases
2. **TGT (Target)** - Retail, clear segments, leases
3. **MCD (McDonald's)** - Restaurants, geographic, leases
4. **SBUX (Starbucks)** - Restaurants, geographic, leases
5. **COST (Costco)** - Retail, geographic, leases
6. **HD (Home Depot)** - Retail, geographic, leases
7. **PG (Procter & Gamble)** - Consumer goods, geographic
8. **KO (Coca-Cola)** - Beverages, geographic
9. **CAT (Caterpillar)** - Manufacturing, geographic
10. **DIS (Disney)** - Media, geographic segments

## Process

1. **Download HTML files** for candidate companies
2. **Extract metrics** using gpt-oss:20b
3. **Identify complete companies** (all 3 metrics)
4. **Build ground truth dataset** from complete companies
5. **Target**: 10 companies with all 3 metrics

## Expected Results

Based on company types:
- **Retail**: ~80% chance of all 3 metrics
- **Restaurants**: ~90% chance of all 3 metrics
- **Consumer Goods**: ~60% chance of all 3 metrics
- **Manufacturing**: ~50% chance of all 3 metrics

## Next Steps

1. Run `find_complete_ground_truth.py` to test 20+ candidates
2. Identify companies with all 3 metrics
3. Create ground truth CSV from complete companies
4. Use for evaluation and model improvement

