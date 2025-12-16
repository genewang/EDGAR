#!/usr/bin/env python3
"""
Convert HTML files from ground_truth_complete.csv to PDFs.
"""

import csv
from pathlib import Path
from playwright.sync_api import sync_playwright
import re

OUTPUT_DIR = "pdfs"


def convert_html_to_pdf(html_path, output_pdf_path):
    """
    Convert an HTML file to PDF using Playwright.
    """
    try:
        html_file = Path(html_path)
        if not html_file.exists():
            print(f"  ✗ HTML file not found: {html_path}")
            return False
            
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
        print(f"  ✗ Error converting {html_path} to PDF: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_company_name_from_ticker(ticker):
    """Map ticker to company name for better PDF naming."""
    # You can expand this mapping as needed
    names = {
        "ADP": "ADP",
        "AMT": "American_Tower",
        "APEI": "American_Public_Education",
        "COST": "Costco",
        "DIS": "Disney",
        "DUK": "Duke_Energy",
        "HD": "Home_Depot",
        "PH": "Parker_Hannifin",
        "SPGI": "S_and_P_Global",
        "TRU": "TransUnion",
    }
    return names.get(ticker, ticker)


def main():
    """
    Main function to convert HTML files from ground_truth_complete.csv to PDFs.
    """
    print("=" * 60)
    print("Converting HTML files from ground_truth_complete.csv to PDFs")
    print("=" * 60)
    print()
    
    # Create output directory
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(exist_ok=True)
    
    # Read ground truth CSV
    ground_truth_file = Path("ground_truth_complete.csv")
    if not ground_truth_file.exists():
        print(f"Error: {ground_truth_file} not found")
        return
    
    pdfs_created = 0
    pdfs_skipped = 0
    pdfs_failed = 0
    
    with open(ground_truth_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticker = row.get('ticker', '').strip()
            html_file = row.get('html_file', '').strip()
            fiscal_year = row.get('fiscal_year', '').strip()
            
            if not ticker or not html_file:
                continue
            
            # Skip empty rows
            if not ticker:
                continue
            
            company_name = get_company_name_from_ticker(ticker)
            
            # Extract year from fiscal_year or use "unknown"
            if fiscal_year and fiscal_year != '':
                try:
                    year = str(int(float(fiscal_year)))
                except:
                    year = "unknown"
            else:
                year = "unknown"
            
            # Create PDF filename
            pdf_filename = f"{ticker}_{company_name}_10K_{year}.pdf"
            pdf_path = output_path / pdf_filename
            
            # Skip if PDF already exists
            if pdf_path.exists():
                print(f"[SKIP] {ticker}: {pdf_filename} already exists")
                pdfs_skipped += 1
                continue
            
            print(f"[{pdfs_created + 1}] Processing {ticker}...")
            print(f"  HTML: {html_file}")
            
            # Convert to PDF
            if convert_html_to_pdf(html_file, pdf_path):
                size_mb = pdf_path.stat().st_size / (1024 * 1024)
                print(f"  ✓ Successfully created: {pdf_filename} ({size_mb:.2f} MB)")
                pdfs_created += 1
            else:
                print(f"  ✗ Failed to create PDF for {ticker}")
                pdfs_failed += 1
            
            print()
    
    print("=" * 60)
    print(f"Conversion complete!")
    print(f"  Created: {pdfs_created} PDF(s)")
    print(f"  Skipped: {pdfs_skipped} PDF(s) (already exist)")
    print(f"  Failed: {pdfs_failed} PDF(s)")
    print("=" * 60)


if __name__ == "__main__":
    main()

