#!/usr/bin/env python3
"""
Extract CIK, Total Revenue, and Net Income from HTML files for all companies
and populate ground_truth_complete.csv.
"""

import csv
import re
from pathlib import Path
from extract_10k_data import BaselineExtractor
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

def extract_cik_from_html(html_path):
    """Extract CIK from HTML file by searching for CIK patterns."""
    try:
        with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Look for CIK patterns in the HTML
        # Pattern 1: "CIK" or "Central Index Key" followed by numbers
        patterns = [
            r'CIK[:\s]*(\d{10})',
            r'Central Index Key[:\s]*(\d{10})',
            r'Commission file number[:\s]*(\d{10})',
            r'File Number[:\s]*(\d{10})',
            r'CIK[:\s]*(\d+)',
            r'cik[:\s]*(\d{10})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                cik = match.group(1)
                # Pad to 10 digits
                return cik.zfill(10)
        
        # Try to extract from file path
        match = re.search(r'/(\d{10})/', str(html_path))
        if match:
            return match.group(1)
        
        return None
    except Exception as e:
        print(f"  Error extracting CIK from {html_path}: {e}")
        return None

def extract_financial_metrics_from_html(html_path, ticker):
    """Extract Total Revenue and Net Income from HTML using baseline extractor."""
    try:
        # Configuration
        openai_key = os.getenv("OPENAI_API_KEY")
        use_ollama = os.getenv("USE_OLLAMA", "").lower() in ("true", "1", "yes") or not openai_key
        ollama_model = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        extractor = BaselineExtractor(
            openai_api_key=openai_key if not use_ollama else None,
            use_ollama=use_ollama,
            ollama_model=ollama_model,
            ollama_base_url=ollama_base_url
        )
        
        result = extractor.extract(html_path, ticker, file_type="html")
        return result.total_revenue, result.net_income
    except Exception as e:
        print(f"  Error extracting metrics from {html_path}: {e}")
        return None, None

def main():
    """Extract features from HTML files and update ground truth CSV."""
    
    ground_truth_file = Path("ground_truth_complete.csv")
    
    if not ground_truth_file.exists():
        print(f"Error: {ground_truth_file} not found")
        return
    
    # Read current ground truth
    df = pd.read_csv(ground_truth_file)
    
    print("=" * 80)
    print("Extracting Features from HTML Files")
    print("Features: CIK, Total Revenue, Net Income")
    print("=" * 80)
    print()
    
    updated_count = 0
    
    for idx, row in df.iterrows():
        ticker = row.get('ticker', '').strip()
        html_file = row.get('html_file', '').strip()
        
        if not ticker or not html_file:
            continue
        
        html_path = Path(html_file)
        
        if not html_path.exists():
            print(f"[{idx + 1}/10] {ticker}: HTML file not found: {html_file}")
            continue
        
        print(f"[{idx + 1}/10] Processing {ticker}...")
        print(f"  HTML: {html_file}")
        
        # Extract CIK
        current_cik = row.get('cik', '')
        if pd.isna(current_cik) or current_cik == '':
            print(f"  Extracting CIK...")
            cik = extract_cik_from_html(html_path)
            if cik:
                df.at[idx, 'cik'] = cik
                print(f"    ✓ CIK: {cik}")
                updated_count += 1
            else:
                print(f"    ✗ CIK: Not found")
        else:
            print(f"  CIK already exists: {current_cik}")
        
        # Extract Total Revenue and Net Income
        current_revenue = row.get('total_revenue', '')
        current_income = row.get('net_income', '')
        
        if pd.isna(current_revenue) or current_revenue == '' or pd.isna(current_income) or current_income == '':
            print(f"  Extracting Total Revenue and Net Income...")
            total_revenue, net_income = extract_financial_metrics_from_html(html_path, ticker)
            
            if total_revenue is not None:
                df.at[idx, 'total_revenue'] = total_revenue
                print(f"    ✓ Total Revenue: {total_revenue}")
                updated_count += 1
            else:
                print(f"    ✗ Total Revenue: Not extracted")
            
            if net_income is not None:
                df.at[idx, 'net_income'] = net_income
                print(f"    ✓ Net Income: {net_income}")
                updated_count += 1
            else:
                print(f"    ✗ Net Income: Not extracted")
        else:
            print(f"  Total Revenue already exists: {current_revenue}")
            print(f"  Net Income already exists: {current_income}")
        
        print()
    
    # Save updated ground truth
    df.to_csv(ground_truth_file, index=False)
    
    print("=" * 80)
    print(f"Extraction complete!")
    print(f"  Updated {updated_count} values")
    print(f"  Ground truth saved to: {ground_truth_file}")
    print("=" * 80)
    
    # Show summary
    print("\nSummary:")
    print("-" * 80)
    complete_count = 0
    for idx, row in df.iterrows():
        ticker = row.get('ticker', '')
        cik = row.get('cik', '')
        revenue = row.get('total_revenue', '')
        income = row.get('net_income', '')
        
        has_cik = pd.notna(cik) and cik != ''
        has_revenue = pd.notna(revenue) and revenue != ''
        has_income = pd.notna(income) and income != ''
        
        complete = has_cik and has_revenue and has_income
        
        status = "✓" if complete else "✗"
        print(f"{status} {ticker}: CIK={has_cik}, Revenue={has_revenue}, Income={has_income}")
        
        if complete:
            complete_count += 1
    
    print(f"\nComplete companies: {complete_count}/10")

if __name__ == "__main__":
    main()

