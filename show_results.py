#!/usr/bin/env python3
"""Display detailed extraction results with ground truth comparison."""

import json
import pandas as pd
from pathlib import Path

# Load results
results_file = Path('complete_extraction_results.json')
with open(results_file, 'r') as f:
    data = json.load(f)

# Load ground truth
gt_file = Path('ground_truth_complete.csv')
df = pd.read_csv(gt_file)

print('=' * 100)
print('DETAILED EXTRACTION RESULTS - COMPARISON WITH GROUND TRUTH')
print('=' * 100)
print()

# Summary statistics
baseline_cik_matches = 0
baseline_rev_matches = 0
baseline_inc_matches = 0
baseline_extracted_cik = 0
baseline_extracted_rev = 0
baseline_extracted_inc = 0

refined_cik_matches = 0
refined_rev_matches = 0
refined_inc_matches = 0
refined_extracted_cik = 0
refined_extracted_rev = 0
refined_extracted_inc = 0

total_companies = len(data)

for ticker, results in sorted(data.items()):
    # Get ground truth
    gt_row = df[df['ticker'] == ticker].iloc[0]
    gt_cik = str(gt_row['cik']).strip() if pd.notna(gt_row['cik']) else None
    gt_revenue = gt_row['total_revenue'] if pd.notna(gt_row['total_revenue']) else None
    gt_income = gt_row['net_income'] if pd.notna(gt_row['net_income']) else None
    
    # Baseline results
    baseline = results.get('baseline', {})
    baseline_cik = baseline.get('cik')
    baseline_revenue = baseline.get('total_revenue')
    baseline_income = baseline.get('net_income')
    
    # Refined results
    refined = results.get('refined', {})
    refined_cik = refined.get('cik')
    refined_revenue = refined.get('total_revenue')
    refined_income = refined.get('net_income')
    
    print(f'{ticker}:')
    print('-' * 100)
    print(f'  Ground Truth:')
    print(f'    CIK: {gt_cik}')
    print(f'    Total Revenue: {gt_revenue}')
    print(f'    Net Income: {gt_income}')
    print()
    
    print(f'  Baseline Extraction:')
    
    # Check CIK match
    if baseline_cik and gt_cik:
        baseline_extracted_cik += 1
        if str(baseline_cik).zfill(10) == str(gt_cik).zfill(10):
            baseline_cik_matches += 1
            cik_match_b = '✓ MATCH'
        else:
            cik_match_b = '✗ MISMATCH'
    else:
        cik_match_b = '✗ NOT EXTRACTED'
    
    # Check Revenue match
    if baseline_revenue and gt_revenue:
        baseline_extracted_rev += 1
        try:
            diff = abs(float(baseline_revenue) - float(gt_revenue))
            rel_error = diff / abs(float(gt_revenue))
            if rel_error <= 0.01:
                baseline_rev_matches += 1
                rev_match_b = f'✓ MATCH (error: {rel_error*100:.2f}%)'
            else:
                rev_match_b = f'✗ MISMATCH (error: {rel_error*100:.2f}%)'
        except:
            rev_match_b = '✗ MISMATCH'
    else:
        rev_match_b = '✗ NOT EXTRACTED'
    
    # Check Income match
    if baseline_income and gt_income:
        baseline_extracted_inc += 1
        try:
            diff = abs(float(baseline_income) - float(gt_income))
            rel_error = diff / abs(float(gt_income))
            if rel_error <= 0.01:
                baseline_inc_matches += 1
                inc_match_b = f'✓ MATCH (error: {rel_error*100:.2f}%)'
            else:
                inc_match_b = f'✗ MISMATCH (error: {rel_error*100:.2f}%)'
        except:
            inc_match_b = '✗ MISMATCH'
    else:
        inc_match_b = '✗ NOT EXTRACTED'
    
    print(f'    CIK: {baseline_cik} - {cik_match_b}')
    print(f'    Total Revenue: {baseline_revenue} - {rev_match_b}')
    print(f'    Net Income: {baseline_income} - {inc_match_b}')
    print()
    
    print(f'  Refined Extraction:')
    
    # Check CIK match
    if refined_cik and gt_cik:
        refined_extracted_cik += 1
        if str(refined_cik).zfill(10) == str(gt_cik).zfill(10):
            refined_cik_matches += 1
            cik_match_r = '✓ MATCH'
        else:
            cik_match_r = '✗ MISMATCH'
    else:
        cik_match_r = '✗ NOT EXTRACTED'
    
    # Check Revenue match
    if refined_revenue and gt_revenue:
        refined_extracted_rev += 1
        try:
            diff = abs(float(refined_revenue) - float(gt_revenue))
            rel_error = diff / abs(float(gt_revenue))
            if rel_error <= 0.01:
                refined_rev_matches += 1
                rev_match_r = f'✓ MATCH (error: {rel_error*100:.2f}%)'
            else:
                rev_match_r = f'✗ MISMATCH (error: {rel_error*100:.2f}%)'
        except:
            rev_match_r = '✗ MISMATCH'
    else:
        rev_match_r = '✗ NOT EXTRACTED'
    
    # Check Income match
    if refined_income and gt_income:
        refined_extracted_inc += 1
        try:
            diff = abs(float(refined_income) - float(gt_income))
            rel_error = diff / abs(float(gt_income))
            if rel_error <= 0.01:
                refined_inc_matches += 1
                inc_match_r = f'✓ MATCH (error: {rel_error*100:.2f}%)'
            else:
                inc_match_r = f'✗ MISMATCH (error: {rel_error*100:.2f}%)'
        except:
            inc_match_r = '✗ MISMATCH'
    else:
        inc_match_r = '✗ NOT EXTRACTED'
    
    print(f'    CIK: {refined_cik} - {cik_match_r}')
    print(f'    Total Revenue: {refined_revenue} - {rev_match_r}')
    print(f'    Net Income: {refined_income} - {inc_match_r}')
    print()
    print()

# Summary
print('=' * 100)
print('SUMMARY STATISTICS')
print('=' * 100)
print()

print('Baseline Extraction:')
print(f'  CIK:')
print(f'    Extracted: {baseline_extracted_cik}/{total_companies} ({baseline_extracted_cik/total_companies*100:.1f}%)')
print(f'    Matched: {baseline_cik_matches}/{total_companies} ({baseline_cik_matches/total_companies*100:.1f}%)')
print(f'  Total Revenue:')
print(f'    Extracted: {baseline_extracted_rev}/{total_companies} ({baseline_extracted_rev/total_companies*100:.1f}%)')
print(f'    Matched: {baseline_rev_matches}/{total_companies} ({baseline_rev_matches/total_companies*100:.1f}%)')
print(f'  Net Income:')
print(f'    Extracted: {baseline_extracted_inc}/{total_companies} ({baseline_extracted_inc/total_companies*100:.1f}%)')
print(f'    Matched: {baseline_inc_matches}/{total_companies} ({baseline_inc_matches/total_companies*100:.1f}%)')
overall_baseline = (baseline_cik_matches + baseline_rev_matches + baseline_inc_matches) / (total_companies * 3) * 100
print(f'  Overall Accuracy: {overall_baseline:.1f}%')
print()

print('Refined Extraction:')
print(f'  CIK:')
print(f'    Extracted: {refined_extracted_cik}/{total_companies} ({refined_extracted_cik/total_companies*100:.1f}%)')
print(f'    Matched: {refined_cik_matches}/{total_companies} ({refined_cik_matches/total_companies*100:.1f}%)')
print(f'  Total Revenue:')
print(f'    Extracted: {refined_extracted_rev}/{total_companies} ({refined_extracted_rev/total_companies*100:.1f}%)')
print(f'    Matched: {refined_rev_matches}/{total_companies} ({refined_rev_matches/total_companies*100:.1f}%)')
print(f'  Net Income:')
print(f'    Extracted: {refined_extracted_inc}/{total_companies} ({refined_extracted_inc/total_companies*100:.1f}%)')
print(f'    Matched: {refined_inc_matches}/{total_companies} ({refined_inc_matches/total_companies*100:.1f}%)')
overall_refined = (refined_cik_matches + refined_rev_matches + refined_inc_matches) / (total_companies * 3) * 100
print(f'  Overall Accuracy: {overall_refined:.1f}%')

