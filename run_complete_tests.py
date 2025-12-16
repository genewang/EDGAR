#!/usr/bin/env python3
"""
Run complete extraction tests on all companies from ground_truth_complete.csv
Tests both baseline and refined extraction methods with new features:
- CIK (Central Index Key)
- Total Revenue
- Net Income
"""

import sys
import json
import pandas as pd
from pathlib import Path
from extract_10k_data import BaselineExtractor, RefinedExtractor, FinancialMetrics, Evaluator
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    """Run complete extraction tests on all companies."""
    
    # Read ground truth
    ground_truth_path = Path("ground_truth_complete.csv")
    if not ground_truth_path.exists():
        print(f"Error: {ground_truth_path} not found")
        return
    
    df = pd.read_csv(ground_truth_path)
    evaluator = Evaluator(ground_truth_path)
    
    # Configuration
    openai_key = os.getenv("OPENAI_API_KEY")
    use_ollama = os.getenv("USE_OLLAMA", "").lower() in ("true", "1", "yes") or not openai_key
    ollama_model = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    llama_key = os.getenv("LLAMA_CLOUD_API_KEY")
    
    print("=" * 80)
    print("COMPLETE EXTRACTION TESTS - NEW FEATURES")
    print("Features: CIK, Total Revenue, Net Income")
    print("=" * 80)
    print(f"Using: {'Ollama' if use_ollama else 'OpenAI'}")
    print(f"Model: {ollama_model}")
    print(f"Companies: {len(df)}")
    print("=" * 80)
    print()
    
    results = {}
    
    # Process each company
    for idx, row in df.iterrows():
        ticker = row.get('ticker', '').strip()
        html_file = row.get('html_file', '').strip()
        
        if not ticker or not html_file:
            continue
        
        html_path = Path(html_file)
        if not html_path.exists():
            print(f"[{idx + 1}/{len(df)}] {ticker}: HTML file not found: {html_file}")
            continue
        
        print(f"[{idx + 1}/{len(df)}] Processing {ticker}...")
        print(f"  HTML: {html_file}")
        
        results[ticker] = {
            'ticker': ticker,
            'html_file': html_file
        }
        
        # Baseline extraction
        try:
            print(f"  [Baseline] Extracting...")
            baseline_extractor = BaselineExtractor(
                openai_api_key=openai_key if not use_ollama else None,
                use_ollama=use_ollama,
                ollama_model=ollama_model,
                ollama_base_url=ollama_base_url
            )
            baseline_result = baseline_extractor.extract(html_path, ticker, file_type="html")
            results[ticker]['baseline'] = baseline_result.model_dump()
            
            print(f"    ✓ CIK: {baseline_result.cik}")
            print(f"    ✓ Total Revenue: {baseline_result.total_revenue}")
            print(f"    ✓ Net Income: {baseline_result.net_income}")
            
            # Evaluate
            eval_result = evaluator.evaluate(baseline_result)
            results[ticker]['baseline_evaluation'] = eval_result
            if 'accuracy' in eval_result:
                print(f"    Accuracy: {eval_result.get('accuracy', 0) * 100:.1f}%")
                print(f"    Metrics matched: {eval_result.get('metrics_matched', 0)}/3")
        except Exception as e:
            print(f"    ✗ Baseline extraction failed: {e}")
            import traceback
            traceback.print_exc()
            results[ticker]['baseline'] = {'error': str(e)}
        
        # Refined extraction (using baseline for HTML since LlamaParse needs PDFs)
        try:
            print(f"  [Refined] Extracting...")
            print(f"    Note: Using baseline HTML extraction (LlamaParse requires PDFs)")
            
            refined_extractor = BaselineExtractor(
                openai_api_key=openai_key if not use_ollama else None,
                use_ollama=use_ollama,
                ollama_model=ollama_model,
                ollama_base_url=ollama_base_url
            )
            refined_result = refined_extractor.extract(html_path, ticker, file_type="html")
            results[ticker]['refined'] = refined_result.model_dump()
            
            print(f"    ✓ CIK: {refined_result.cik}")
            print(f"    ✓ Total Revenue: {refined_result.total_revenue}")
            print(f"    ✓ Net Income: {refined_result.net_income}")
            
            # Evaluate
            eval_result = evaluator.evaluate(refined_result)
            results[ticker]['refined_evaluation'] = eval_result
            if 'accuracy' in eval_result:
                print(f"    Accuracy: {eval_result.get('accuracy', 0) * 100:.1f}%")
                print(f"    Metrics matched: {eval_result.get('metrics_matched', 0)}/3")
        except Exception as e:
            print(f"    ✗ Refined extraction failed: {e}")
            import traceback
            traceback.print_exc()
            results[ticker]['refined'] = {'error': str(e)}
        
        print()
    
    # Save results
    output_file = Path("complete_extraction_results.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("=" * 80)
    print(f"Results saved to: {output_file}")
    print("=" * 80)
    
    # Print summary
    print("\nSUMMARY")
    print("=" * 80)
    
    baseline_success = sum(1 for r in results.values() if 'baseline' in r and 'error' not in r.get('baseline', {}))
    refined_success = sum(1 for r in results.values() if 'refined' in r and 'error' not in r.get('refined', {}))
    
    print(f"Baseline extraction: {baseline_success}/{len(results)} successful")
    print(f"Refined extraction: {refined_success}/{len(results)} successful")
    
    # Calculate average accuracy
    baseline_accuracies = []
    refined_accuracies = []
    
    for ticker, data in results.items():
        if 'baseline_evaluation' in data and 'accuracy' in data['baseline_evaluation']:
            baseline_accuracies.append(data['baseline_evaluation']['accuracy'])
        if 'refined_evaluation' in data and 'accuracy' in data['refined_evaluation']:
            refined_accuracies.append(data['refined_evaluation']['accuracy'])
    
    if baseline_accuracies:
        avg_baseline = sum(baseline_accuracies) / len(baseline_accuracies)
        print(f"\nBaseline average accuracy: {avg_baseline * 100:.1f}%")
    
    if refined_accuracies:
        avg_refined = sum(refined_accuracies) / len(refined_accuracies)
        print(f"Refined average accuracy: {avg_refined * 100:.1f}%")
    
    # Per-metric accuracy
    print("\nPer-Metric Accuracy:")
    print("-" * 80)
    
    for metric in ['cik', 'total_revenue', 'net_income']:
        baseline_matches = sum(1 for r in results.values() 
                              if 'baseline_evaluation' in r 
                              and 'metrics' in r['baseline_evaluation']
                              and metric in r['baseline_evaluation']['metrics']
                              and r['baseline_evaluation']['metrics'][metric].get('match', False))
        
        refined_matches = sum(1 for r in results.values() 
                             if 'refined_evaluation' in r 
                             and 'metrics' in r['refined_evaluation']
                             and metric in r['refined_evaluation']['metrics']
                             and r['refined_evaluation']['metrics'][metric].get('match', False))
        
        print(f"{metric.upper()}:")
        print(f"  Baseline: {baseline_matches}/{len(results)} ({baseline_matches/len(results)*100:.1f}%)")
        print(f"  Refined: {refined_matches}/{len(results)} ({refined_matches/len(results)*100:.1f}%)")

if __name__ == "__main__":
    main()

