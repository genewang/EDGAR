#!/usr/bin/env python3
"""
Extract financial metrics directly from HTML files using gpt-oss:20b.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the extractor from the main script
sys.path.insert(0, str(Path(__file__).parent))
from extract_10k_data import BaselineExtractor, FinancialMetrics

def find_html_files(base_dir="sec-edgar-filings"):
    """Find all primary-document.html files and map them to tickers."""
    base_path = Path(base_dir)
    html_files = {}
    
    # Pattern: sec-edgar-filings/{TICKER}/10-K/{FILING_ID}/primary-document.html
    for html_file in base_path.glob("*/10-K/*/primary-document.html"):
        ticker = html_file.parent.parent.parent.name
        html_files[ticker] = html_file
    
    return html_files

def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract financial metrics from 10-K HTML files')
    parser.add_argument('--html-dir', type=str, default='sec-edgar-filings',
                       help='Directory containing HTML files (default: sec-edgar-filings)')
    parser.add_argument('--output', type=str, default='html_extraction_results.json',
                       help='Output file for extraction results')
    parser.add_argument('--use-ollama', action='store_true', default=True,
                       help='Use local Ollama server (default: True)')
    parser.add_argument('--ollama-model', type=str, default='gpt-oss:20b',
                       help='Ollama model name (default: gpt-oss:20b)')
    parser.add_argument('--ollama-base-url', type=str, default='http://localhost:11434',
                       help='Ollama server base URL (default: http://localhost:11434)')
    
    args = parser.parse_args()
    
    # Find HTML files
    html_files = find_html_files(args.html_dir)
    
    if not html_files:
        print(f"Error: No HTML files found in {args.html_dir}")
        print("Expected structure: {html_dir}/{TICKER}/10-K/{FILING_ID}/primary-document.html")
        sys.exit(1)
    
    print(f"Found {len(html_files)} HTML files to process")
    print("=" * 80)
    
    # Initialize extractor
    print(f"Initializing extractor with model: {args.ollama_model}")
    extractor = BaselineExtractor(
        openai_api_key=None,  # Using Ollama
        use_ollama=True,
        ollama_model=args.ollama_model,
        ollama_base_url=args.ollama_base_url
    )
    
    results = {}
    
    # Process each HTML file
    for ticker, html_path in sorted(html_files.items()):
        print(f"\nProcessing {ticker}: {html_path.name}")
        print(f"  File: {html_path}")
        
        results[ticker] = {}
        
        try:
            print(f"  Running HTML extraction...")
            result = extractor.extract(html_path, ticker, file_type="html")
            results[ticker]['html'] = result.model_dump()
            print(f"  ✓ HTML extraction complete")
        except Exception as e:
            print(f"  ✗ HTML extraction failed: {e}")
            import traceback
            traceback.print_exc()
            results[ticker]['html'] = {'error': str(e)}
    
    # Save results
    output_path = Path(args.output)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n{'=' * 80}")
    print(f"Results saved to {output_path}")
    print("=" * 80)
    
    # Print summary
    print("\nEXTRACTION SUMMARY")
    print("=" * 80)
    successful = sum(1 for r in results.values() if 'error' not in r.get('html', {}))
    print(f"Successfully processed: {successful}/{len(results)} companies")
    
    # Count extractions
    revenue_count = sum(1 for r in results.values() 
                       if r.get('html', {}).get('north_america_revenue') is not None)
    depr_count = sum(1 for r in results.values() 
                    if r.get('html', {}).get('depreciation_amortization') is not None)
    lease_count = sum(1 for r in results.values() 
                     if r.get('html', {}).get('lease_liabilities') is not None)
    
    print(f"\nExtraction Rates:")
    print(f"  • North America Revenue:        {revenue_count}/{len(results)} ({revenue_count/len(results)*100:.1f}%)")
    print(f"  • Depreciation & Amortization:  {depr_count}/{len(results)} ({depr_count/len(results)*100:.1f}%)")
    print(f"  • Lease Liabilities:            {lease_count}/{len(results)} ({lease_count/len(results)*100:.1f}%)")

if __name__ == "__main__":
    main()

