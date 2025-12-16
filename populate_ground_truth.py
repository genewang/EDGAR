#!/usr/bin/env python3
"""
Helper script to populate ground truth CSV with values from PDFs.

This script helps you manually enter ground truth values by providing
a structured interface. You'll need to open each PDF and extract the values.
"""

import pandas as pd
from pathlib import Path
import sys

def main():
    """Interactive script to populate ground truth."""
    ground_truth_path = Path("ground_truth.csv")
    
    # Load existing ground truth or create new
    if ground_truth_path.exists():
        df = pd.read_csv(ground_truth_path)
    else:
        # Create template
        pdf_dir = Path("pdfs")
        pdf_files = list(pdf_dir.glob("*.pdf"))
        tickers = [f.stem.split('_')[0] for f in pdf_files]
        
        df = pd.DataFrame({
            'ticker': tickers,
            'cik': [None] * len(tickers),
            'total_revenue': [None] * len(tickers),
            'net_income': [None] * len(tickers)
        })
    
    print("=" * 60)
    print("Ground Truth Data Entry")
    print("=" * 60)
    print("\nFor each company, you'll need to extract:")
    print("1. CIK (Central Index Key) - from filing header/cover page")
    print("2. Total Revenue (millions USD) - from Income Statement")
    print("3. Net Income (millions USD) - from Income Statement")
    print("\nOpen the PDFs in the 'pdfs' directory to find these values.")
    print("=" * 60)
    
    for idx, row in df.iterrows():
        ticker = row['ticker']
        pdf_path = Path("pdfs") / f"{ticker}_*.pdf"
        pdf_files = list(Path("pdfs").glob(f"{ticker}_*.pdf"))
        
        if pdf_files:
            pdf_name = pdf_files[0].name
        else:
            pdf_name = "Not found"
        
        print(f"\n[{idx + 1}/{len(df)}] {ticker} - {pdf_name}")
        print("-" * 60)
        
        # CIK
        current_cik = row.get('cik', '')
        if pd.notna(current_cik) and current_cik != '':
            print(f"Current CIK: {current_cik}")
        cik = input("CIK (10-digit identifier, or press Enter to skip): ").strip()
        if cik:
            # Normalize CIK to 10 digits
            cik_clean = cik.replace('-', '').replace(' ', '').strip()
            try:
                cik_int = int(cik_clean)
                df.at[idx, 'cik'] = str(cik_int).zfill(10)
            except ValueError:
                print(f"  Invalid CIK format, skipping...")
        
        # Total Revenue
        current_rev = row.get('total_revenue', '')
        if pd.notna(current_rev) and current_rev != '':
            print(f"Current Total Revenue: {current_rev}")
        total_rev = input("Total Revenue (millions USD, or press Enter to skip): ").strip()
        if total_rev:
            try:
                df.at[idx, 'total_revenue'] = float(total_rev)
            except ValueError:
                print(f"  Invalid number, skipping...")
        
        # Net Income
        current_ni = row.get('net_income', '')
        if pd.notna(current_ni) and current_ni != '':
            print(f"Current Net Income: {current_ni}")
        net_inc = input("Net Income (millions USD, or press Enter to skip): ").strip()
        if net_inc:
            try:
                df.at[idx, 'net_income'] = float(net_inc)
            except ValueError:
                print(f"  Invalid number, skipping...")
    
    # Save
    df.to_csv(ground_truth_path, index=False)
    print(f"\n{'=' * 60}")
    print(f"Ground truth saved to {ground_truth_path}")
    print(f"Filled {df.notna().sum().sum() - 1} values out of {len(df) * 3} total")
    print("=" * 60)

if __name__ == "__main__":
    main()

