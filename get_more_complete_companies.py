#!/usr/bin/env python3
"""
Get more companies to reach 10 with complete financial metrics.
Focuses on retail, restaurants, and consumer goods companies.
"""

import os
import sys
import json
from pathlib import Path
from sec_edgar_downloader import Downloader
from dotenv import load_dotenv

load_dotenv()

# Additional candidates - focusing on high-probability companies
ADDITIONAL_CANDIDATES = [
    # More Retail
    "LOW",   # Lowe's - retail, geographic segments
    "BBY",   # Best Buy - retail, geographic
    "TJX",   # TJX Companies - retail, geographic
    
    # More Restaurants
    "CMG",   # Chipotle - restaurants, leases, geographic
    "YUM",   # Yum Brands - restaurants, leases
    "DPZ",   # Domino's - restaurants, leases
    
    # Consumer Goods
    "CL",    # Colgate-Palmolive - consumer goods, geographic
    "KMB",   # Kimberly-Clark - consumer goods, geographic
    "HRL",   # Hormel Foods - consumer goods
    
    # Other good candidates
    "F",     # Ford - manufacturing, geographic
    "GM",    # General Motors - manufacturing, geographic
    "UPS",   # UPS - logistics, geographic, leases
    "FDX",   # FedEx - logistics, geographic, leases
    "LMT",   # Lockheed Martin - aerospace, geographic
    "RTX",   # Raytheon - aerospace, geographic
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
    """Download and test additional companies."""
    print("=" * 80)
    print("GETTING MORE COMPLETE COMPANIES")
    print("=" * 80)
    print()
    
    # Load existing results
    existing_file = Path("candidate_companies_results.json")
    if existing_file.exists():
        with open(existing_file) as f:
            existing_results = json.load(f)
    else:
        existing_results = {}
    
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
    
    results = existing_results.copy()
    complete_companies = [t for t, d in results.items() if d.get('complete')]
    
    print(f"Already have {len(complete_companies)} complete companies")
    print(f"Testing {len(ADDITIONAL_CANDIDATES)} additional candidates...")
    print()
    
    # Test additional companies
    for i, ticker in enumerate(ADDITIONAL_CANDIDATES, 1):
        if ticker in results:
            print(f"[{i}/{len(ADDITIONAL_CANDIDATES)}] {ticker} - Already tested, skipping")
            continue
            
        print(f"[{i}/{len(ADDITIONAL_CANDIDATES)}] Testing {ticker}...")
        
        # Download HTML if not already present
        html_file = None
        ticker_dir = Path(DOWNLOAD_DIR) / ticker / "10-K"
        if ticker_dir.exists():
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
                print(f"    Revenue: ${metrics.get('north_america_revenue', 0):,.0f}M")
                print(f"    Depreciation: ${metrics.get('depreciation_amortization', 0):,.0f}M")
                print(f"    Lease: ${metrics.get('lease_liabilities', 0):,.0f}M")
                
                if len(complete_companies) >= 10:
                    print(f"\n✓ Reached target of 10 complete companies!")
                    break
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
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"\nTotal complete companies: {len(complete_companies)}")
    
    if complete_companies:
        print(f"\n✓ COMPLETE COMPANIES (All 3 metrics):")
        for ticker in sorted(complete_companies):
            metrics = results[ticker]['metrics']
            print(f"  {ticker}:")
            print(f"    Revenue: ${metrics.get('north_america_revenue', 0):,.0f}M")
            print(f"    Depreciation: ${metrics.get('depreciation_amortization', 0):,.0f}M")
            print(f"    Lease: ${metrics.get('lease_liabilities', 0):,.0f}M")
            print(f"    File: {results[ticker]['html_file']}")
    
    # Save results
    output_file = "candidate_companies_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to: {output_file}")
    
    # Create ground truth CSV
    if len(complete_companies) >= 10:
        print(f"\nCreating ground truth CSV for {len(complete_companies)} complete companies...")
        import pandas as pd
        
        ground_truth_data = []
        for ticker in sorted(complete_companies)[:10]:  # Take first 10
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
        print(f"✓ Ground truth saved to: {gt_file}")
        print(f"\nYou now have 10 companies with complete data for ground truth!")
    else:
        print(f"\n⚠️  Need {10 - len(complete_companies)} more complete companies to reach target of 10")

if __name__ == "__main__":
    main()

