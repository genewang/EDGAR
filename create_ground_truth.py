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
        # Extract CIK from HTML file path if available
        cik = ''
        html_file = data.get('html_file', '')
        if html_file:
            import re
            match = re.search(r'/(\d{10})/', html_file)
            if match:
                cik = match.group(1)
        
        ground_truth_data.append({
            'ticker': ticker,
            'cik': cik,
            'total_revenue': metrics.get('total_revenue'),
            'net_income': metrics.get('net_income'),
            'html_file': html_file,
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
        # Extract CIK from HTML file path if available
        cik = ''
        html_file = data.get('html_file', '')
        if html_file:
            import re
            match = re.search(r'/(\d{10})/', html_file)
            if match:
                cik = match.group(1)
        
        print(f"{ticker}:")
        print(f"  CIK: {cik}")
        print(f"  Total Revenue: ${metrics.get('total_revenue', 0):,.0f}M")
        print(f"  Net Income: ${metrics.get('net_income', 0):,.0f}M")
        print(f"  File: {html_file}")
        print()
    
    # Create summary document
    summary_file = "ground_truth_summary.md"
    with open(summary_file, 'w') as f:
        f.write("# Ground Truth Dataset Summary\n\n")
        f.write(f"**Total Companies**: {len(complete_companies)}\n\n")
        f.write("## Companies with All 3 Metrics\n\n")
        f.write("| Ticker | CIK | Total Revenue (M) | Net Income (M) | Fiscal Year |\n")
        f.write("|--------|-----|------------------|----------------|-------------|\n")
        
        for ticker, data in complete_companies:
            metrics = data['metrics']
            # Extract CIK from HTML file path if available
            cik = ''
            html_file = data.get('html_file', '')
            if html_file:
                import re
                match = re.search(r'/(\d{10})/', html_file)
                if match:
                    cik = match.group(1)
            
            f.write(f"| {ticker} | ")
            f.write(f"{cik} | ")
            f.write(f"${metrics.get('total_revenue', 0):,.0f} | ")
            f.write(f"${metrics.get('net_income', 0):,.0f} | ")
            f.write(f"{metrics.get('fiscal_year', 'N/A')} |\n")
        
        f.write("\n## Selection Criteria\n\n")
        f.write("Companies were selected based on:\n")
        f.write("1. **CIK**: Central Index Key from SEC filing header\n")
        f.write("2. **Total Revenue**: From Income Statement (Statement of Operations)\n")
        f.write("3. **Net Income**: From Income Statement (Statement of Operations)\n")
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

