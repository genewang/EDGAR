#!/usr/bin/env python3
"""
Compare baseline extraction results against ground truth.
"""

import json
import pandas as pd
from pathlib import Path

def format_value(val):
    """Format value for display."""
    if val is None:
        return "—"
    if isinstance(val, float):
        return f"${val:,.0f}M"
    return str(val)

def compare_results(baseline_file="baseline_extraction_results.json", 
                   ground_truth_file="ground_truth.csv"):
    """Compare extraction results with ground truth."""
    
    # Load baseline results
    with open(baseline_file, 'r') as f:
        results = json.load(f)
    
    # Load ground truth
    gt_path = Path(ground_truth_file)
    if gt_path.exists():
        gt = pd.read_csv(gt_path)
        gt.set_index('ticker', inplace=True)
        gt_available = True
    else:
        gt_available = False
        print(f"⚠️  Ground truth file '{ground_truth_file}' not found.")
    
    print("=" * 100)
    print("BASELINE EXTRACTION RESULTS - COMPARISON WITH GROUND TRUTH")
    print("=" * 100)
    print()
    
    # Prepare comparison data
    comparison_rows = []
    metrics_stats = {
        'north_america_revenue': {'extracted': 0, 'total': 0, 'matches': 0},
        'depreciation_amortization': {'extracted': 0, 'total': 0, 'matches': 0},
        'lease_liabilities': {'extracted': 0, 'total': 0, 'matches': 0}
    }
    
    for ticker in sorted(results.keys()):
        baseline = results[ticker].get('baseline', {})
        
        row = {
            'Ticker': ticker,
            'Extracted Revenue': baseline.get('north_america_revenue'),
            'Extracted Depreciation': baseline.get('depreciation_amortization'),
            'Extracted Lease': baseline.get('lease_liabilities'),
        }
        
        if gt_available and ticker in gt.index:
            gt_row = gt.loc[ticker]
            gt_revenue = gt_row.get('north_america_revenue')
            gt_depr = gt_row.get('depreciation_amortization')
            gt_lease = gt_row.get('lease_liabilities')
            
            row['GT Revenue'] = gt_revenue if pd.notna(gt_revenue) else None
            row['GT Depreciation'] = gt_depr if pd.notna(gt_depr) else None
            row['GT Lease'] = gt_lease if pd.notna(gt_lease) else None
            
            # Check matches (within 1% tolerance)
            tolerance = 0.01
            for metric in ['north_america_revenue', 'depreciation_amortization', 'lease_liabilities']:
                extracted_val = baseline.get(metric)
                gt_val = gt_row.get(metric)
                
                if pd.notna(gt_val) and gt_val != '':
                    metrics_stats[metric]['total'] += 1
                    if extracted_val is not None:
                        metrics_stats[metric]['extracted'] += 1
                        if abs(extracted_val - float(gt_val)) / abs(float(gt_val)) <= tolerance:
                            metrics_stats[metric]['matches'] += 1
        else:
            row['GT Revenue'] = None
            row['GT Depreciation'] = None
            row['GT Lease'] = None
        
        comparison_rows.append(row)
    
    # Display table
    print(f"{'Ticker':<8} {'Revenue (Extracted)':<20} {'Revenue (GT)':<15} {'Depreciation (Extracted)':<25} {'Depreciation (GT)':<20} {'Lease (Extracted)':<20} {'Lease (GT)':<15}")
    print("-" * 100)
    
    for row in comparison_rows:
        ticker = row['Ticker']
        rev_ext = format_value(row['Extracted Revenue'])
        rev_gt = format_value(row['GT Revenue'])
        depr_ext = format_value(row['Extracted Depreciation'])
        depr_gt = format_value(row['GT Depreciation'])
        lease_ext = format_value(row['Extracted Lease'])
        lease_gt = format_value(row['GT Lease'])
        
        # Add match indicators
        if row['GT Revenue'] is not None and row['Extracted Revenue'] is not None:
            if abs(row['Extracted Revenue'] - float(row['GT Revenue'])) / abs(float(row['GT Revenue'])) <= 0.01:
                rev_ext += " ✓"
            else:
                rev_ext += " ✗"
        
        if row['GT Depreciation'] is not None and row['Extracted Depreciation'] is not None:
            if abs(row['Extracted Depreciation'] - float(row['GT Depreciation'])) / abs(float(row['GT Depreciation'])) <= 0.01:
                depr_ext += " ✓"
            else:
                depr_ext += " ✗"
        
        if row['GT Lease'] is not None and row['Extracted Lease'] is not None:
            if abs(row['Extracted Lease'] - float(row['GT Lease'])) / abs(float(row['GT Lease'])) <= 0.01:
                lease_ext += " ✓"
            else:
                lease_ext += " ✗"
        
        print(f"{ticker:<8} {rev_ext:<20} {rev_gt:<15} {depr_ext:<25} {depr_gt:<20} {lease_ext:<20} {lease_gt:<15}")
    
    print()
    print("=" * 100)
    print("EXTRACTION STATISTICS")
    print("=" * 100)
    
    total_companies = len(results)
    extracted_revenue = sum(1 for r in comparison_rows if r['Extracted Revenue'] is not None)
    extracted_depr = sum(1 for r in comparison_rows if r['Extracted Depreciation'] is not None)
    extracted_lease = sum(1 for r in comparison_rows if r['Extracted Lease'] is not None)
    
    print(f"Total Companies Processed: {total_companies}")
    print()
    print("Extraction Rates (Baseline Method):")
    print(f"  • North America Revenue:        {extracted_revenue}/{total_companies} ({extracted_revenue/total_companies*100:.1f}%)")
    print(f"  • Depreciation & Amortization:  {extracted_depr}/{total_companies} ({extracted_depr/total_companies*100:.1f}%)")
    print(f"  • Lease Liabilities:            {extracted_lease}/{total_companies} ({extracted_lease/total_companies*100:.1f}%)")
    
    if gt_available:
        print()
        print("Accuracy (vs Ground Truth, within 1% tolerance):")
        for metric, stats in metrics_stats.items():
            if stats['total'] > 0:
                accuracy = stats['matches'] / stats['total'] * 100
                print(f"  • {metric.replace('_', ' ').title()}: {stats['matches']}/{stats['total']} ({accuracy:.1f}%)")
            else:
                print(f"  • {metric.replace('_', ' ').title()}: No ground truth data available")
    else:
        print()
        print("⚠️  Ground truth file is empty or not available.")
        print("   To enable accuracy comparison, populate ground_truth.csv with actual values.")
    
    print()
    print("=" * 100)
    print("DETAILED RESULTS BY COMPANY")
    print("=" * 100)
    
    for row in comparison_rows:
        ticker = row['Ticker']
        print(f"\n{ticker}:")
        print(f"  Revenue:        {format_value(row['Extracted Revenue'])} (GT: {format_value(row['GT Revenue'])})")
        print(f"  Depreciation:   {format_value(row['Extracted Depreciation'])} (GT: {format_value(row['GT Depreciation'])})")
        print(f"  Lease:          {format_value(row['Extracted Lease'])} (GT: {format_value(row['GT Lease'])})")
    
    print()
    print("=" * 100)

if __name__ == "__main__":
    compare_results()

