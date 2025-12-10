#!/usr/bin/env python3
"""
Automated SEC EDGAR 10-K PDF Downloader

This script downloads 10-K filings from SEC EDGAR and converts them to PDFs.
It replicates the manual process of:
1. Finding the CIK for a company
2. Filtering for 10-K filings
3. Locating the primary HTML document
4. Converting it to PDF
"""

import os
import sys
from pathlib import Path
from sec_edgar_downloader import Downloader
from playwright.sync_api import sync_playwright
import re

# Configuration
COMPANY_TICKERS = [
    "AAPL",   # Apple Inc.
    "MSFT",   # Microsoft Corporation
    "GOOGL",  # Alphabet Inc.
    "AMZN",   # Amazon.com Inc.
    "TSLA",   # Tesla, Inc.
    "META",   # Meta Platforms Inc.
    "NVDA",   # NVIDIA Corporation
    "JPM",    # JPMorgan Chase & Co.
    "V",      # Visa Inc.
    "JNJ",    # Johnson & Johnson
]

DOWNLOAD_DIR = "sec-edgar-filings"
OUTPUT_DIR = "pdfs"
COMPANY_NAME = "EDGAR PDF Downloader"  # Identifier for SEC (can be any name)
EMAIL = "user@example.com"  # Email identifier for SEC (can be any email)
NUM_PDFS_TO_GET = 10


def find_primary_document(filing_dir):
    """
    Find the primary HTML document in a filing directory.
    The primary document is usually the first .htm file listed.
    """
    filing_path = Path(filing_dir)
    
    # Look for .htm or .html files
    html_files = list(filing_path.glob("*.htm")) + list(filing_path.glob("*.html"))
    
    if not html_files:
        return None
    
    # Sort to get consistent ordering (primary is usually first alphabetically)
    html_files.sort()
    
    # The primary document is typically the one without "cover" or "graphic" in the name
    for html_file in html_files:
        name_lower = html_file.name.lower()
        if "cover" not in name_lower and "graphic" not in name_lower:
            return html_file
    
    # If no "clean" file found, return the first one
    return html_files[0]


def convert_html_to_pdf(html_path, output_pdf_path):
    """
    Convert an HTML file to PDF using Playwright.
    Playwright uses a headless browser for accurate HTML/CSS rendering.
    """
    try:
        html_file = Path(html_path)
        html_url = f"file://{html_file.absolute()}"
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(html_url, wait_until='networkidle')
            
            # Generate PDF with proper formatting
            page.pdf(
                path=str(output_pdf_path),
                format='Letter',
                margin={
                    'top': '0.75in',
                    'right': '0.75in',
                    'bottom': '0.75in',
                    'left': '0.75in'
                },
                print_background=True
            )
            browser.close()
        
        return True
    except Exception as e:
        print(f"Error converting {html_path} to PDF: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_company_name_from_ticker(ticker):
    """Map ticker to company name for better PDF naming."""
    names = {
        "AAPL": "Apple",
        "MSFT": "Microsoft",
        "GOOGL": "Alphabet",
        "AMZN": "Amazon",
        "TSLA": "Tesla",
        "META": "Meta",
        "NVDA": "NVIDIA",
        "JPM": "JPMorgan",
        "V": "Visa",
        "JNJ": "Johnson_Johnson",
    }
    return names.get(ticker, ticker)


def main():
    """
    Main function to download 10-K filings and convert them to PDFs.
    """
    print("=" * 60)
    print("SEC EDGAR 10-K PDF Downloader")
    print("=" * 60)
    print()
    
    # Create output directory
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(exist_ok=True)
    
    # Initialize downloader
    print(f"Initializing SEC EDGAR downloader...")
    print(f"Company: {COMPANY_NAME}")
    print(f"Email: {EMAIL}")
    print()
    
    try:
        dl = Downloader(COMPANY_NAME, EMAIL)
    except Exception as e:
        print(f"Error initializing downloader: {e}")
        sys.exit(1)
    
    pdfs_created = 0
    ticker_index = 0
    
    # Download 10-K filings until we have enough PDFs
    while pdfs_created < NUM_PDFS_TO_GET and ticker_index < len(COMPANY_TICKERS):
        ticker = COMPANY_TICKERS[ticker_index]
        company_name = get_company_name_from_ticker(ticker)
        
        print(f"[{pdfs_created + 1}/{NUM_PDFS_TO_GET}] Processing {ticker} ({company_name})...")
        
        try:
            # Download the most recent 10-K filing
            # We'll download 1 at a time to get variety across companies
            dl.get("10-K", ticker, limit=1, download_details=True)
            
            # Find the downloaded filing
            ticker_dir = Path(DOWNLOAD_DIR) / ticker / "10-K"
            
            if not ticker_dir.exists():
                print(f"  Warning: No filings found for {ticker}")
                ticker_index += 1
                continue
            
            # Get the most recent filing directory
            filing_dirs = sorted(ticker_dir.iterdir(), key=os.path.getmtime, reverse=True)
            
            if not filing_dirs:
                print(f"  Warning: No filing directories found for {ticker}")
                ticker_index += 1
                continue
            
            # Process the most recent filing
            for filing_dir in filing_dirs:
                if not filing_dir.is_dir():
                    continue
                
                primary_doc = find_primary_document(filing_dir)
                
                if not primary_doc:
                    print(f"  Warning: No primary document found in {filing_dir}")
                    continue
                
                # Extract year from filing directory name (usually contains date)
                filing_name = filing_dir.name
                year_match = re.search(r'(\d{4})', filing_name)
                year = year_match.group(1) if year_match else "unknown"
                
                # Create PDF filename
                pdf_filename = f"{ticker}_{company_name}_10K_{year}.pdf"
                pdf_path = output_path / pdf_filename
                
                # Skip if PDF already exists
                if pdf_path.exists():
                    print(f"  PDF already exists: {pdf_filename}")
                    pdfs_created += 1
                    break
                
                print(f"  Found primary document: {primary_doc.name}")
                print(f"  Converting to PDF: {pdf_filename}...")
                
                # Convert to PDF
                if convert_html_to_pdf(primary_doc, pdf_path):
                    print(f"  ✓ Successfully created: {pdf_filename}")
                    pdfs_created += 1
                else:
                    print(f"  ✗ Failed to create PDF for {ticker}")
                
                # Only process one filing per ticker in this iteration
                break
            
            ticker_index += 1
            
        except Exception as e:
            print(f"  Error processing {ticker}: {e}")
            ticker_index += 1
            continue
        
        print()
    
    print("=" * 60)
    print(f"Download complete! Created {pdfs_created} PDF(s) in '{OUTPUT_DIR}' directory.")
    print("=" * 60)
    
    # List created PDFs
    if pdfs_created > 0:
        print("\nCreated PDFs:")
        for pdf_file in sorted(output_path.glob("*.pdf")):
            size_mb = pdf_file.stat().st_size / (1024 * 1024)
            print(f"  - {pdf_file.name} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()

