#!/usr/bin/env python3
"""
Find companies with complete financial metrics for ground truth dataset.
Downloads HTML files for companies likely to have all 3 metrics clearly reported.
"""

import os
import sys
import json
from pathlib import Path
from sec_edgar_downloader import Downloader
from dotenv import load_dotenv

load_dotenv()

# Companies likely to have all 3 metrics clearly reported:
# - Geographic segments (North America revenue)
# - Depreciation (capital-intensive or manufacturing)
# - Lease liabilities (retail, restaurants, or capital leases)
CANDIDATE_COMPANIES = [
    # Retail (clear geographic segments + leases)
    "WMT",   # Walmart - retail, clear geographic segments
    "TGT",   # Target - retail, geographic segments
    "COST",  # Costco - retail, geographic segments
    "HD",    # Home Depot - retail, geographic segments
    
    # Tech with geographic segments
    "INTC",  # Intel - manufacturing, geographic segments
    "ORCL",  # Oracle - software, geographic segments
    "CSCO",  # Cisco - networking, geographic segments
    "IBM",   # IBM - tech services, geographic segments
    
    # Consumer goods (geographic segments)
    "PG",    # Procter & Gamble - consumer goods, geographic
    "KO",    # Coca-Cola - beverages, geographic segments
    "PEP",   # PepsiCo - beverages, geographic segments
    "NKE",   # Nike - apparel, geographic segments
    
    # Manufacturing (depreciation + geographic)
    "CAT",   # Caterpillar - manufacturing, geographic
    "DE",    # Deere & Company - manufacturing, geographic
    "BA",    # Boeing - aerospace, geographic
    
    # Restaurants (leases + geographic)
    "MCD",   # McDonald's - restaurants, leases, geographic
    "SBUX",  # Starbucks - restaurants, leases, geographic
    
    # Other good candidates
    "DIS",   # Disney - media, geographic segments
    "NFLX",  # Netflix - streaming, geographic segments
    "WMT",   # Walmart (already listed but good)
    "XOM",   # Exxon Mobil - energy, geographic segments
    "CVX",   # Chevron - energy, geographic segments
]

DOWNLOAD_DIR = "sec-edgar-filings"
COMPANY_NAME = "EDGAR Ground Truth Builder"
EMAIL = "research@example.com"

def download_company_html(ticker, downloader):
    """Download the most recent 10-K HTML file for a company."""
    try:
        print(f"  Downloading 10-K for {ticker}...")
        downloader.get("10-K", ticker, limit=1, download_details=True)
        
        # Find the downloaded HTML file
        ticker_dir = Path(DOWNLOAD_DIR) / ticker / "10-K"
        if not ticker_dir.exists():
            return None
        
        # Get most recent filing
        filing_dirs = sorted(ticker_dir.iterdir(), key=os.path.getmtime, reverse=True)
        if not filing_dirs:
            return None
        
        # Find primary document
        for filing_dir in filing_dirs:
            html_files = list(filing_dir.glob("*.html")) + list(filing_dir.glob("*.htm"))
            for html_file in sorted(html_files):
                name_lower = html_file.name.lower()
                if "cover" not in name_lower and "graphic" not in name_lower:
                    return html_file
        
        return None
    except Exception as e:
        print(f"  Error downloading {ticker}: {e}")
        return None

def main():
    """Download HTML files and test extraction to find complete datasets."""
    print("=" * 80)
    print("FINDING COMPANIES WITH COMPLETE FINANCIAL METRICS")
    print("=" * 80)
    print()
    print(f"Testing {len(CANDIDATE_COMPANIES)} candidate companies...")
    print()
    
    # Initialize downloader
    try:
        dl = Downloader(COMPANY_NAME, EMAIL)
    except Exception as e:
        print(f"Error initializing downloader: {e}")
        sys.exit(1)
    
    # Import extractor
    sys.path.insert(0, str(Path(__file__).parent))
    from extract_10k_data import BaselineExtractor
    
    # Initialize extractor
    print("Initializing extractor with gpt-oss:20b...")
    extractor = BaselineExtractor(
        openai_api_key=None,
        use_ollama=True,
        ollama_model="gpt-oss:20b",
        ollama_base_url="http://localhost:11434"
    )
    print()
    
    results = {}
    complete_companies = []
    
    # Test each company
    for i, ticker in enumerate(CANDIDATE_COMPANIES, 1):
        print(f"[{i}/{len(CANDIDATE_COMPANIES)}] Testing {ticker}...")
        
        # Download HTML if not already present
        html_file = None
        ticker_dir = Path(DOWNLOAD_DIR) / ticker / "10-K"
        if ticker_dir.exists():
            # Check if we already have HTML
            for filing_dir in sorted(ticker_dir.iterdir(), key=os.path.getmtime, reverse=True):
                html_files = list(filing_dir.glob("*.html")) + list(filing_dir.glob("*.htm"))
                for hf in sorted(html_files):
                    name_lower = hf.name.lower()
                    if "cover" not in name_lower and "graphic" not in name_lower:
                        html_file = hf
                        break
                if html_file:
                    break
        
        if not html_file:
            html_file = download_company_html(ticker, dl)
        
        if not html_file:
            print(f"  ✗ Could not find HTML file for {ticker}")
            results[ticker] = {'status': 'no_file'}
            continue
        
        print(f"  Found: {html_file.name}")
        
        # Try extraction
        try:
            print(f"  Extracting metrics...")
            result = extractor.extract(html_file, ticker, file_type="html")
            metrics = result.model_dump()
            
            # Check completeness
            has_revenue = metrics.get('north_america_revenue') is not None
            has_depreciation = metrics.get('depreciation_amortization') is not None
            has_lease = metrics.get('lease_liabilities') is not None
            
            complete = has_revenue and has_depreciation and has_lease
            
            results[ticker] = {
                'status': 'complete' if complete else 'partial',
                'html_file': str(html_file),
                'metrics': metrics,
                'has_revenue': has_revenue,
                'has_depreciation': has_depreciation,
                'has_lease': has_lease,
                'complete': complete
            }
            
            if complete:
                complete_companies.append(ticker)
                print(f"  ✓ COMPLETE - All 3 metrics extracted!")
            else:
                missing = []
                if not has_revenue:
                    missing.append("Revenue")
                if not has_depreciation:
                    missing.append("Depreciation")
                if not has_lease:
                    missing.append("Lease")
                print(f"  ⚠️  Partial - Missing: {', '.join(missing)}")
            
        except Exception as e:
            print(f"  ✗ Extraction failed: {e}")
            results[ticker] = {'status': 'error', 'error': str(e)}
        
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nTotal companies tested: {len(CANDIDATE_COMPANIES)}")
    print(f"Complete (all 3 metrics): {len(complete_companies)}")
    print(f"Partial: {sum(1 for r in results.values() if r.get('status') == 'partial')}")
    print(f"Errors/No file: {sum(1 for r in results.values() if r.get('status') in ['error', 'no_file'])}")
    
    if complete_companies:
        print(f"\n✓ COMPLETE COMPANIES (All 3 metrics):")
        for ticker in complete_companies:
            metrics = results[ticker]['metrics']
            print(f"  {ticker}:")
            print(f"    Revenue: ${metrics.get('north_america_revenue', 0):,.0f}M")
            print(f"    Depreciation: ${metrics.get('depreciation_amortization', 0):,.0f}M")
            print(f"    Lease: ${metrics.get('lease_liabilities', 0):,.0f}M")
    
    # Save results
    output_file = "candidate_companies_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to: {output_file}")
    
    # Create ground truth CSV template
    if complete_companies:
        print(f"\nCreating ground truth CSV for {len(complete_companies)} complete companies...")
        import pandas as pd
        
        ground_truth_data = []
        for ticker in complete_companies:
            metrics = results[ticker]['metrics']
            ground_truth_data.append({
                'ticker': ticker,
                'north_america_revenue': metrics.get('north_america_revenue'),
                'depreciation_amortization': metrics.get('depreciation_amortization'),
                'lease_liabilities': metrics.get('lease_liabilities')
            })
        
        df = pd.DataFrame(ground_truth_data)
        gt_file = "ground_truth_complete.csv"
        df.to_csv(gt_file, index=False)
        print(f"Ground truth saved to: {gt_file}")
        print(f"\nYou now have {len(complete_companies)} companies with complete data for ground truth!")

if __name__ == "__main__":
    main()

