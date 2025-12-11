#!/usr/bin/env python3
"""
Create ground truth CSV from companies with all 3 metrics.
Also creates a summary document explaining the selection.
"""

import json
import pandas as pd
from pathlib import Path

def main():
    """Create ground truth dataset from complete companies."""
    
    # Load results
    results_file = Path("candidate_companies_results.json")
    if not results_file.exists():
        print("Error: candidate_companies_results.json not found")
        print("Run find_complete_ground_truth.py first")
        return
    
    with open(results_file) as f:
        results = json.load(f)
    
    # Find complete companies
    complete_companies = []
    for ticker, data in results.items():
        if data.get('complete'):
            complete_companies.append((ticker, data))
    
    # Sort by ticker
    complete_companies.sort(key=lambda x: x[0])
    
    print("=" * 80)
    print("CREATING GROUND TRUTH DATASET")
    print("=" * 80)
    print()
    print(f"Found {len(complete_companies)} companies with all 3 metrics")
    print()
    
    if len(complete_companies) == 0:
        print("No complete companies found!")
        return
    
    # Create ground truth data
    ground_truth_data = []
    for ticker, data in complete_companies:
        metrics = data['metrics']
        ground_truth_data.append({
            'ticker': ticker,
            'north_america_revenue': metrics.get('north_america_revenue'),
            'depreciation_amortization': metrics.get('depreciation_amortization'),
            'lease_liabilities': metrics.get('lease_liabilities'),
            'html_file': data.get('html_file', ''),
            'fiscal_year': metrics.get('fiscal_year', '')
        })
    
    # Create DataFrame
    df = pd.DataFrame(ground_truth_data)
    
    # Save CSV
    output_file = "ground_truth_complete.csv"
    df.to_csv(output_file, index=False)
    print(f"✓ Ground truth saved to: {output_file}")
    print()
    
    # Display summary
    print("COMPLETE COMPANIES:")
    print("-" * 80)
    for ticker, data in complete_companies:
        metrics = data['metrics']
        print(f"{ticker}:")
        print(f"  Revenue: ${metrics.get('north_america_revenue', 0):,.0f}M")
        print(f"  Depreciation: ${metrics.get('depreciation_amortization', 0):,.0f}M")
        print(f"  Lease: ${metrics.get('lease_liabilities', 0):,.0f}M")
        print(f"  File: {data.get('html_file', 'N/A')}")
        print()
    
    # Create summary document
    summary_file = "ground_truth_summary.md"
    with open(summary_file, 'w') as f:
        f.write("# Ground Truth Dataset Summary\n\n")
        f.write(f"**Total Companies**: {len(complete_companies)}\n\n")
        f.write("## Companies with All 3 Metrics\n\n")
        f.write("| Ticker | Revenue (M) | Depreciation (M) | Lease (M) | Fiscal Year |\n")
        f.write("|--------|------------|------------------|-----------|-------------|\n")
        
        for ticker, data in complete_companies:
            metrics = data['metrics']
            f.write(f"| {ticker} | ")
            f.write(f"${metrics.get('north_america_revenue', 0):,.0f} | ")
            f.write(f"${metrics.get('depreciation_amortization', 0):,.0f} | ")
            f.write(f"${metrics.get('lease_liabilities', 0):,.0f} | ")
            f.write(f"{metrics.get('fiscal_year', 'N/A')} |\n")
        
        f.write("\n## Selection Criteria\n\n")
        f.write("Companies were selected based on:\n")
        f.write("1. **North America Revenue**: Clearly reported in segment/geographic tables\n")
        f.write("2. **Depreciation & Amortization**: From cash flow statement\n")
        f.write("3. **Lease Liabilities**: From balance sheet (current + non-current)\n")
        f.write("\n## Company Types\n\n")
        f.write("- **Retail**: WMT, HD, COST (clear geographic segments + leases)\n")
        f.write("- **Media/Entertainment**: DIS (geographic segments + leases)\n")
        f.write("- **Automotive**: TSLA (geographic segments + leases)\n")
        f.write("\n## Usage\n\n")
        f.write("Use `ground_truth_complete.csv` for:\n")
        f.write("- Model evaluation\n")
        f.write("- Accuracy benchmarking\n")
        f.write("- Extraction quality assessment\n")
    
    print(f"✓ Summary saved to: {summary_file}")
    print()
    
    if len(complete_companies) >= 10:
        print("✓ SUCCESS: You have 10+ companies with complete data!")
        print(f"  Use the first 10 from {output_file} for your ground truth dataset")
    else:
        print(f"⚠️  You have {len(complete_companies)} complete companies")
        print(f"  Consider running get_more_complete_companies.py to find more")

if __name__ == "__main__":
    main()

