#!/usr/bin/env python3
"""
Test extraction on converted HTML files from PDFs using new features:
- CIK (Central Index Key)
- Total Revenue
- Net Income
"""

import sys
import json
from pathlib import Path
from extract_10k_data import BaselineExtractor, RefinedExtractor, FinancialMetrics, Evaluator
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    """Test extraction on HTML files with new features."""
    
    # HTML files to test (for APEI as example)
    html_files = [
        {
            'name': 'Basic HTML Conversion',
            'path': Path("pdfs/APEI_American_Public_Education_10K_2024_converted.html"),
            'ticker': 'APEI'
        },
        {
            'name': 'Advanced HTML Conversion',
            'path': Path("pdfs/APEI_American_Public_Education_10K_2024_converted_advanced.html"),
            'ticker': 'APEI'
        }
    ]
    
    # Ground truth for APEI (if available)
    ground_truth_path = Path("ground_truth_complete.csv")
    evaluator = Evaluator(ground_truth_path) if ground_truth_path.exists() else None
    
    # Configuration
    openai_key = os.getenv("OPENAI_API_KEY")
    use_ollama = os.getenv("USE_OLLAMA", "").lower() in ("true", "1", "yes") or not openai_key
    ollama_model = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    llama_key = os.getenv("LLAMA_CLOUD_API_KEY")
    
    if use_ollama:
        print("Using Ollama for extraction")
    else:
        print("Using OpenAI for extraction")
    
    results = {}
    
    print("=" * 80)
    print("Testing Extraction on Converted HTML Files - NEW FEATURES")
    print("Features: CIK, Total Revenue, Net Income")
    print("=" * 80)
    print()
    
    for html_info in html_files:
        html_file = html_info['path']
        ticker = html_info['ticker']
        conversion_type = html_info['name']
        
        if not html_file.exists():
            print(f"Warning: {html_file} not found, skipping...")
            continue
        
        print(f"\n{'=' * 80}")
        print(f"Processing: {conversion_type}")
        print(f"File: {html_file.name}")
        print(f"{'=' * 80}")
        
        file_key = f"{ticker}_{conversion_type.replace(' ', '_').lower()}"
        results[file_key] = {
            'conversion_type': conversion_type,
            'ticker': ticker,
            'html_file': str(html_file)
        }
        
        # Baseline extraction
        try:
            print(f"\n[Baseline] Extracting from {html_file.name}...")
            baseline_extractor = BaselineExtractor(
                openai_api_key=openai_key if not use_ollama else None,
                use_ollama=use_ollama,
                ollama_model=ollama_model,
                ollama_base_url=ollama_base_url
            )
            baseline_result = baseline_extractor.extract(html_file, ticker, file_type="html")
            results[file_key]['baseline'] = baseline_result.model_dump()
            print(f"  ✓ Baseline extraction complete")
            print(f"    CIK: {baseline_result.cik}")
            print(f"    Total Revenue: {baseline_result.total_revenue}")
            print(f"    Net Income: {baseline_result.net_income}")
            
            # Evaluate if ground truth available
            if evaluator:
                eval_result = evaluator.evaluate(baseline_result)
                results[file_key]['baseline_evaluation'] = eval_result
                if 'accuracy' in eval_result:
                    print(f"    Accuracy: {eval_result.get('accuracy', 0) * 100:.1f}%")
        except Exception as e:
            print(f"  ✗ Baseline extraction failed: {e}")
            import traceback
            traceback.print_exc()
            results[file_key]['baseline'] = {'error': str(e)}
        
        # Refined extraction
        try:
            print(f"\n[Refined] Extracting from {html_file.name}...")
            print(f"  Note: Refined extraction (LlamaParse) only works with PDFs.")
            print(f"  Using baseline approach with refined LLM settings...")
            
            # Use baseline extractor but with the refined extractor's LLM
            baseline_extractor_for_refined = BaselineExtractor(
                openai_api_key=openai_key if not use_ollama else None,
                use_ollama=use_ollama,
                ollama_model=ollama_model,
                ollama_base_url=ollama_base_url
            )
            refined_result = baseline_extractor_for_refined.extract(html_file, ticker, file_type="html")
            results[file_key]['refined'] = refined_result.model_dump()
            print(f"  ✓ Refined extraction complete (using baseline HTML extraction)")
            print(f"    CIK: {refined_result.cik}")
            print(f"    Total Revenue: {refined_result.total_revenue}")
            print(f"    Net Income: {refined_result.net_income}")
            
            # Evaluate if ground truth available
            if evaluator:
                eval_result = evaluator.evaluate(refined_result)
                results[file_key]['refined_evaluation'] = eval_result
                if 'accuracy' in eval_result:
                    print(f"    Accuracy: {eval_result.get('accuracy', 0) * 100:.1f}%")
        except Exception as e:
            print(f"  ✗ Refined extraction failed: {e}")
            import traceback
            traceback.print_exc()
            results[file_key]['refined'] = {'error': str(e)}
    
    # Save results
    output_file = Path("html_extraction_results_new_features.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n{'=' * 80}")
    print(f"Results saved to: {output_file}")
    print(f"{'=' * 80}")
    
    # Print summary
    print(f"\n{'=' * 80}")
    print("SUMMARY - Extraction Results")
    print(f"{'=' * 80}")
    
    if evaluator:
        print(f"\nGround Truth for {ticker}:")
        gt = evaluator.ground_truth.loc[ticker]
        print(f"  CIK: {gt.get('cik', 'N/A')}")
        print(f"  Total Revenue: {gt.get('total_revenue', 'N/A')}")
        print(f"  Net Income: {gt.get('net_income', 'N/A')}")
    
    print(f"\nExtraction Results:")
    for file_key, file_results in results.items():
        print(f"\n  {file_results.get('conversion_type', file_key)}:")
        for method in ['baseline', 'refined']:
            if method in file_results and 'error' not in file_results[method]:
                method_results = file_results[method]
                print(f"    {method.capitalize()}:")
                print(f"      CIK: {method_results.get('cik', 'N/A')}")
                print(f"      Total Revenue: {method_results.get('total_revenue', 'N/A')}")
                print(f"      Net Income: {method_results.get('net_income', 'N/A')}")
                
                eval_key = f"{method}_evaluation"
                if eval_key in file_results:
                    eval_result = file_results[eval_key]
                    if 'accuracy' in eval_result:
                        acc = eval_result.get('accuracy', 0) * 100
                        print(f"      Accuracy: {acc:.1f}%")
                        
                        # Show metric-by-metric results
                        if 'metrics' in eval_result:
                            for metric, metric_result in eval_result['metrics'].items():
                                match = metric_result.get('match', False)
                                status = "✓" if match else "✗"
                                extracted = metric_result.get('extracted', 'N/A')
                                ground_truth = metric_result.get('ground_truth', 'N/A')
                                print(f"        {status} {metric}: {extracted} vs {ground_truth}")


if __name__ == "__main__":
    main()


