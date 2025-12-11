#!/usr/bin/env python3
"""
Compare different Ollama models for financial document extraction.
Tests multiple models on the same PDFs and compares results.
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

def run_extraction(model_name, output_file):
    """Run extraction with a specific model."""
    print(f"\n{'='*80}")
    print(f"Testing model: {model_name}")
    print(f"{'='*80}")
    
    cmd = [
        "python", "extract_10k_data.py",
        "--mode", "baseline",
        "--pdf-dir", "pdfs",
        "--use-ollama",
        "--ollama-model", model_name,
        "--output", output_file
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        if result.returncode == 0:
            print(f"✓ Successfully completed extraction with {model_name}")
            return True
        else:
            print(f"✗ Extraction failed with {model_name}")
            print(f"Error: {result.stderr[:500]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"✗ Extraction timed out with {model_name}")
        return False
    except Exception as e:
        print(f"✗ Error running extraction: {e}")
        return False

def compare_results(model1_file, model2_file, model1_name, model2_name):
    """Compare results from two models."""
    print(f"\n{'='*80}")
    print(f"COMPARISON: {model1_name} vs {model2_name}")
    print(f"{'='*80}\n")
    
    # Load results
    with open(model1_file, 'r') as f:
        results1 = json.load(f)
    
    with open(model2_file, 'r') as f:
        results2 = json.load(f)
    
    # Compare metrics
    metrics = ['north_america_revenue', 'depreciation_amortization', 'lease_liabilities']
    
    comparison = {
        'model1': model1_name,
        'model2': model2_name,
        'companies': {}
    }
    
    for ticker in sorted(set(list(results1.keys()) + list(results2.keys()))):
        baseline1 = results1.get(ticker, {}).get('baseline', {})
        baseline2 = results2.get(ticker, {}).get('baseline', {})
        
        comp = {
            'ticker': ticker,
            'model1_values': {},
            'model2_values': {},
            'matches': 0,
            'total': 0
        }
        
        for metric in metrics:
            val1 = baseline1.get(metric)
            val2 = baseline2.get(metric)
            
            comp['model1_values'][metric] = val1
            comp['model2_values'][metric] = val2
            
            if val1 is not None or val2 is not None:
                comp['total'] += 1
                if val1 is not None and val2 is not None:
                    # Check if values match (within 1% tolerance)
                    if abs(val1 - val2) / max(abs(val1), abs(val2), 1) <= 0.01:
                        comp['matches'] += 1
        
        comparison['companies'][ticker] = comp
    
    # Print comparison table
    print(f"{'Ticker':<8} {'Metric':<30} {model1_name[:20]:<20} {model2_name[:20]:<20} {'Match':<8}")
    print("-" * 100)
    
    total_extractions_model1 = 0
    total_extractions_model2 = 0
    total_matches = 0
    total_comparable = 0
    
    for ticker, comp in comparison['companies'].items():
        for metric in metrics:
            val1 = comp['model1_values'][metric]
            val2 = comp['model2_values'][metric]
            
            if val1 is not None:
                total_extractions_model1 += 1
            if val2 is not None:
                total_extractions_model2 += 1
            
            if val1 is not None and val2 is not None:
                total_comparable += 1
                match = "✓" if abs(val1 - val2) / max(abs(val1), abs(val2), 1) <= 0.01 else "✗"
                if match == "✓":
                    total_matches += 1
                
                val1_str = f"${val1:,.0f}M" if val1 else "—"
                val2_str = f"${val2:,.0f}M" if val2 else "—"
                print(f"{ticker:<8} {metric.replace('_', ' ').title():<30} {val1_str:<20} {val2_str:<20} {match:<8}")
            elif val1 is not None or val2 is not None:
                val1_str = f"${val1:,.0f}M" if val1 else "—"
                val2_str = f"${val2:,.0f}M" if val2 else "—"
                print(f"{ticker:<8} {metric.replace('_', ' ').title():<30} {val1_str:<20} {val2_str:<20} {'—':<8}")
    
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    print(f"\nExtraction Rates:")
    print(f"  {model1_name}: {total_extractions_model1} extractions across all metrics")
    print(f"  {model2_name}: {total_extractions_model2} extractions across all metrics")
    
    if total_comparable > 0:
        agreement = (total_matches / total_comparable) * 100
        print(f"\nAgreement Rate: {total_matches}/{total_comparable} ({agreement:.1f}%)")
        print("  (Values match within 1% tolerance)")
    else:
        print("\nNo comparable values found (models extracted different metrics)")
    
    # Save comparison
    comparison_file = f"model_comparison_{model1_name.replace(':', '_')}_vs_{model2_name.replace(':', '_')}.json"
    with open(comparison_file, 'w') as f:
        json.dump(comparison, f, indent=2, default=str)
    
    print(f"\nComparison saved to: {comparison_file}")
    
    return comparison

def main():
    """Main comparison function."""
    models_to_test = [
        ("gpt-oss:20b", "baseline_gptoss20b_results.json"),
        ("deepseek-coder-v2", "baseline_deepseek_results.json")
    ]
    
    print("="*80)
    print("MODEL COMPARISON TEST")
    print("="*80)
    print(f"Testing {len(models_to_test)} models on all PDFs")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Run extractions
    for model_name, output_file in models_to_test:
        success = run_extraction(model_name, output_file)
        if success:
            results[model_name] = output_file
        else:
            print(f"⚠️  Skipping {model_name} due to extraction failure")
    
    # Compare results
    if len(results) >= 2:
        model_names = list(results.keys())
        compare_results(
            results[model_names[0]],
            results[model_names[1]],
            model_names[0],
            model_names[1]
        )
    else:
        print("\n⚠️  Need at least 2 successful extractions to compare")
    
    print(f"\n{'='*80}")
    print(f"Comparison complete at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

if __name__ == "__main__":
    main()

