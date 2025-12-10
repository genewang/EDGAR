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
            'north_america_revenue': [None] * len(tickers),
            'depreciation_amortization': [None] * len(tickers),
            'lease_liabilities': [None] * len(tickers)
        })
    
    print("=" * 60)
    print("Ground Truth Data Entry")
    print("=" * 60)
    print("\nFor each company, you'll need to extract:")
    print("1. North America Revenue (millions USD)")
    print("2. Depreciation & Amortization (millions USD)")
    print("3. Total Lease Liabilities (millions USD)")
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
        
        # North America Revenue
        current_na = row.get('north_america_revenue', '')
        if pd.notna(current_na) and current_na != '':
            print(f"Current North America Revenue: {current_na}")
        na_rev = input("North America Revenue (millions USD, or press Enter to skip): ").strip()
        if na_rev:
            try:
                df.at[idx, 'north_america_revenue'] = float(na_rev)
            except ValueError:
                print(f"  Invalid number, skipping...")
        
        # Depreciation & Amortization
        current_da = row.get('depreciation_amortization', '')
        if pd.notna(current_da) and current_da != '':
            print(f"Current Depreciation & Amortization: {current_da}")
        dep_amort = input("Depreciation & Amortization (millions USD, or press Enter to skip): ").strip()
        if dep_amort:
            try:
                df.at[idx, 'depreciation_amortization'] = float(dep_amort)
            except ValueError:
                print(f"  Invalid number, skipping...")
        
        # Lease Liabilities
        current_lease = row.get('lease_liabilities', '')
        if pd.notna(current_lease) and current_lease != '':
            print(f"Current Lease Liabilities: {current_lease}")
        lease_liab = input("Total Lease Liabilities (millions USD, or press Enter to skip): ").strip()
        if lease_liab:
            try:
                df.at[idx, 'lease_liabilities'] = float(lease_liab)
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

