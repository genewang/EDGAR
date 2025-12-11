# Ground Truth Dataset Summary

**Total Companies**: 7

## Companies with All 3 Metrics

| Ticker | Revenue (M) | Depreciation (M) | Lease (M) | Fiscal Year |
|--------|------------|------------------|-----------|-------------|
| ADP | $18,179 | $582 | $422 | None |
| COST | $200 | $2 | $3 | None |
| DIS | $61,888 | $5,326 | $3,235 | 2025 |
| HD | $153,108 | $3,283 | $8,907 | 2024 |
| SPGI | $8,640 | $1,160 | $644 | 2024 |
| TRU | $3,238 | $718 | $42 | None |
| WMT | $557,622 | $1,458 | $14,324 | 2025 |

## Selection Criteria

Companies were selected based on:
1. **North America Revenue**: Clearly reported in segment/geographic tables
2. **Depreciation & Amortization**: From cash flow statement
3. **Lease Liabilities**: From balance sheet (current + non-current)

## Company Types

- **Retail**: WMT, HD, COST (clear geographic segments + leases)
- **Media/Entertainment**: DIS (geographic segments + leases)
- **Automotive**: TSLA (geographic segments + leases)

## Usage

Use `ground_truth_complete.csv` for:
- Model evaluation
- Accuracy benchmarking
- Extraction quality assessment
