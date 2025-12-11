#!/usr/bin/env python3
"""Display deepseek-coder-v2 extraction results."""

import json
from pathlib import Path

def format_value(val):
    """Format value for display."""
    if val is None:
        return "—"
    if isinstance(val, float):
        return f"${val:,.0f}M"
    return str(val)

def show_deepseek_results():
    """Display deepseek-coder-v2 results."""
    
    results_file = "baseline_deepseek_results.json"
    
    if not Path(results_file).exists():
        print(f"Error: {results_file} not found")
        return
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    print("=" * 100)
    print("DEEPSEEK-CODER-V2 EXTRACTION RESULTS")
    print("=" * 100)
    print()
    
    # Statistics
    total_companies = len(results)
    successful = 0
    errors = 0
    timeouts = 0
    other_errors = 0
    
    extracted_revenue = 0
    extracted_depr = 0
    extracted_lease = 0
    
    print(f"{'Ticker':<8} {'Status':<20} {'Revenue':<20} {'Depreciation':<20} {'Lease':<20}")
    print("-" * 100)
    
    for ticker in sorted(results.keys()):
        baseline = results[ticker].get('baseline', {})
        
        if 'error' in baseline:
            error_msg = baseline['error']
            if 'timed out' in error_msg.lower():
                status = "⏱️  TIMEOUT"
                timeouts += 1
            elif 'stopped' in error_msg.lower() or '500' in error_msg:
                status = "❌ ERROR"
                other_errors += 1
            else:
                status = f"❌ {error_msg[:15]}"
                other_errors += 1
            errors += 1
            
            print(f"{ticker:<8} {status:<20} {'—':<20} {'—':<20} {'—':<20}")
        else:
            status = "✓ SUCCESS"
            successful += 1
            
            revenue = baseline.get('north_america_revenue')
            depreciation = baseline.get('depreciation_amortization')
            lease = baseline.get('lease_liabilities')
            
            if revenue is not None:
                extracted_revenue += 1
            if depreciation is not None:
                extracted_depr += 1
            if lease is not None:
                extracted_lease += 1
            
            print(f"{ticker:<8} {status:<20} {format_value(revenue):<20} {format_value(depreciation):<20} {format_value(lease):<20}")
    
    print()
    print("=" * 100)
    print("SUMMARY STATISTICS")
    print("=" * 100)
    print(f"\nProcessing Status:")
    print(f"  ✓ Successful:        {successful}/{total_companies} ({successful/total_companies*100:.1f}%)")
    print(f"  ⏱️  Timeouts:          {timeouts}/{total_companies} ({timeouts/total_companies*100:.1f}%)")
    print(f"  ❌ Other Errors:      {other_errors}/{total_companies} ({other_errors/total_companies*100:.1f}%)")
    print(f"  Total Errors:        {errors}/{total_companies} ({errors/total_companies*100:.1f}%)")
    
    if successful > 0:
        print(f"\nExtraction Rates (from {successful} successful extractions):")
        print(f"  • North America Revenue:        {extracted_revenue}/{successful} ({extracted_revenue/successful*100:.1f}%)")
        print(f"  • Depreciation & Amortization:  {extracted_depr}/{successful} ({extracted_depr/successful*100:.1f}%)")
        print(f"  • Lease Liabilities:            {extracted_lease}/{successful} ({extracted_lease/successful*100:.1f}%)")
    
    print()
    print("=" * 100)
    print("SUCCESSFUL EXTRACTIONS (DETAILED)")
    print("=" * 100)
    
    for ticker in sorted(results.keys()):
        baseline = results[ticker].get('baseline', {})
        if 'error' not in baseline:
            print(f"\n{ticker}:")
            print(f"  Revenue:        {format_value(baseline.get('north_america_revenue'))}")
            print(f"  Depreciation:   {format_value(baseline.get('depreciation_amortization'))}")
            print(f"  Lease:          {format_value(baseline.get('lease_liabilities'))}")
            if baseline.get('fiscal_year'):
                print(f"  Fiscal Year:    {baseline.get('fiscal_year')}")
    
    print()
    print("=" * 100)
    print("OBSERVATIONS")
    print("=" * 100)
    print("\n⚠️  Deepseek-coder-v2 experienced significant issues:")
    print("  • Multiple timeouts during processing")
    print("  • Model runner crashes (status code: 500)")
    print("  • Only 2 out of 10 companies processed successfully")
    print("\n💡 This suggests deepseek-coder-v2 may not be suitable for this task due to:")
    print("  • Resource limitations (memory/CPU)")
    print("  • Model stability issues with long documents")
    print("  • Timeout issues with complex queries")
    print("\n✅ Recommendation: Stick with gpt-oss:20b or try llama3.1:8b for better stability")

if __name__ == "__main__":
    show_deepseek_results()

