#!/usr/bin/env python3
"""
Test education, publishing, recreational, and travel companies to find complete financial metrics.
These companies often have:
- Geographic segments (especially travel companies)
- Depreciation (from facilities, equipment, content assets)
- Lease liabilities (office leases, facility leases, retail locations)
"""

import os
import sys
import json
from pathlib import Path
from sec_edgar_downloader import Downloader
from dotenv import load_dotenv

load_dotenv()

# Education, Publishing, Recreational, and Travel companies
EDUCATION_PUBLISHING_TRAVEL_CANDIDATES = [
    # Travel Companies
    "BKNG",  # Booking Holdings - already tested, but retry
    "EXPE",  # Expedia - already tested, but retry
    "TCOM",  # Trip.com - travel, geographic segments
    "ABNB",  # Airbnb - travel, geographic segments
    "MAR",   # Marriott - hotels, geographic segments, leases
    "HLT",   # Hilton - hotels, geographic segments, leases
    "H",     # Hyatt - hotels, geographic segments, leases
    "WH",    # Wyndham - hotels, geographic segments, leases
    
    # Education Companies
    "APEI",  # American Public Education - education services
    "LAUR",  # Laureate Education - education services
    "LRN",   # Stride - education services
    "COUR",  # Coursera - online education, geographic
    
    # Publishing & Media
    "NWSA",  # News Corp - publishing, geographic
    "FOXA",  # Fox Corporation - media/publishing, geographic
    "PARA",  # Paramount Global - media/publishing, geographic
    "WBD",   # Warner Bros Discovery - media/publishing, geographic
    
    # Recreational & Entertainment
    "LVS",   # Las Vegas Sands - casinos, geographic segments, leases
    "WYNN",  # Wynn Resorts - casinos, geographic segments, leases
    "MGM",   # MGM Resorts - casinos, geographic segments, leases
    "CZR",   # Caesars Entertainment - casinos, geographic segments, leases
    "NCLH",  # Norwegian Cruise Line - travel/recreation, geographic
    "RCL",   # Royal Caribbean - travel/recreation, geographic
    "CCL",   # Carnival - travel/recreation, geographic
    
    # Other Travel/Recreation
    "LULU",  # Lululemon - retail/recreation, geographic
    "NKE",   # Nike - already tested, but retry
    "UAA",   # Under Armour - retail/recreation, geographic
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
    """Test education, publishing, recreational, and travel companies."""
    print("=" * 80)
    print("TESTING EDUCATION, PUBLISHING, RECREATIONAL & TRAVEL COMPANIES")
    print("=" * 80)
    print()
    print(f"Testing {len(EDUCATION_PUBLISHING_TRAVEL_CANDIDATES)} companies...")
    print()
    print("These companies often have:")
    print("  - Geographic segments (especially travel companies)")
    print("  - Depreciation (from facilities, equipment, content assets)")
    print("  - Lease liabilities (office leases, facility leases, retail locations)")
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
    print(f"Target: 10 complete companies")
    print(f"Need: {max(0, 10 - len(complete_companies))} more")
    print()
    
    # Test companies
    new_complete = []
    for i, ticker in enumerate(EDUCATION_PUBLISHING_TRAVEL_CANDIDATES, 1):
        # Skip if already complete
        if ticker in results and results[ticker].get('complete'):
            print(f"[{i}/{len(EDUCATION_PUBLISHING_TRAVEL_CANDIDATES)}] {ticker} - Already complete, skipping")
            continue
        
        print(f"[{i}/{len(EDUCATION_PUBLISHING_TRAVEL_CANDIDATES)}] Testing {ticker}...")
        
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
                new_complete.append(ticker)
                complete_companies.append(ticker)
                print(f"  ✓✓✓ COMPLETE - All 3 metrics extracted!")
                print(f"    Revenue: ${metrics.get('north_america_revenue', 0):,.0f}M")
                print(f"    Depreciation: ${metrics.get('depreciation_amortization', 0):,.0f}M")
                print(f"    Lease: ${metrics.get('lease_liabilities', 0):,.0f}M")
                
                if len(complete_companies) >= 10:
                    print(f"\n🎉 SUCCESS! Reached target of 10 complete companies!")
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
                # Show what we found
                if has_revenue:
                    print(f"    ✓ Revenue: ${metrics.get('north_america_revenue', 0):,.0f}M")
                if has_depreciation:
                    print(f"    ✓ Depreciation: ${metrics.get('depreciation_amortization', 0):,.0f}M")
                if has_lease:
                    print(f"    ✓ Lease: ${metrics.get('lease_liabilities', 0):,.0f}M")
            
        except Exception as e:
            print(f"  ✗ Extraction failed: {e}")
            results[ticker] = {'status': 'error', 'error': str(e)}
        
        print()
    
    # Summary
    print("=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"\nTotal complete companies: {len(complete_companies)}")
    print(f"New complete companies found: {len(new_complete)}")
    
    if new_complete:
        print(f"\n✓ NEW COMPLETE COMPANIES:")
        for ticker in new_complete:
            metrics = results[ticker]['metrics']
            print(f"  {ticker}:")
            print(f"    Revenue: ${metrics.get('north_america_revenue', 0):,.0f}M")
            print(f"    Depreciation: ${metrics.get('depreciation_amortization', 0):,.0f}M")
            print(f"    Lease: ${metrics.get('lease_liabilities', 0):,.0f}M")
            print(f"    File: {results[ticker]['html_file']}")
    
    if complete_companies:
        print(f"\n✓ ALL COMPLETE COMPANIES ({len(complete_companies)}):")
        for ticker in sorted(complete_companies):
            metrics = results[ticker]['metrics']
            print(f"  {ticker}: ${metrics.get('north_america_revenue', 0):,.0f}M revenue, "
                  f"${metrics.get('depreciation_amortization', 0):,.0f}M depreciation, "
                  f"${metrics.get('lease_liabilities', 0):,.0f}M lease")
    
    # Save results
    output_file = "candidate_companies_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to: {output_file}")
    
    # Update ground truth if we have 10+
    if len(complete_companies) >= 10:
        print(f"\n🎉 Creating updated ground truth CSV...")
        import pandas as pd
        
        ground_truth_data = []
        for ticker in sorted(complete_companies)[:10]:  # Take first 10
            metrics = results[ticker]['metrics']
            ground_truth_data.append({
                'ticker': ticker,
                'north_america_revenue': metrics.get('north_america_revenue'),
                'depreciation_amortization': metrics.get('depreciation_amortization'),
                'lease_liabilities': metrics.get('lease_liabilities'),
                'html_file': results[ticker].get('html_file', ''),
                'fiscal_year': metrics.get('fiscal_year', '')
            })
        
        df = pd.DataFrame(ground_truth_data)
        gt_file = "ground_truth_complete.csv"
        df.to_csv(gt_file, index=False)
        print(f"✓ Ground truth saved to: {gt_file}")
        print(f"\n✅ You now have 10 companies with complete data for ground truth!")
    else:
        print(f"\n⚠️  Currently have {len(complete_companies)} complete companies")
        print(f"   Need {10 - len(complete_companies)} more to reach target of 10")
        
        # Show close companies
        close = []
        for ticker, data in results.items():
            if data.get('status') == 'partial':
                count = sum([
                    data.get('has_revenue', False),
                    data.get('has_depreciation', False),
                    data.get('has_lease', False)
                ])
                if count == 2:
                    close.append(ticker)
        
        if close:
            print(f"\n💡 Found {len(close)} companies with 2 of 3 metrics - consider refined extraction:")
            for ticker in sorted(close)[:5]:
                print(f"   - {ticker}")

if __name__ == "__main__":
    main()

