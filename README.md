# SEC EDGAR 10-K PDF Downloader

Automated tool to download 10-K filings from SEC EDGAR and convert them to PDFs. This replicates the manual process of finding company CIKs, filtering for 10-K filings, locating primary documents, and converting them to PDF format.

## Overview

This project implements **Approach A: The "Free & Flexible" Stack** using:
- `sec-edgar-downloader`: Python library to download SEC EDGAR filings
- `playwright`: Headless browser for accurate HTML to PDF conversion

## Prerequisites

1. **Python 3.7+**
2. **Playwright browsers** (installed automatically on first run)

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install chromium
```

3. (Optional) Update identification info in `download_10k_pdfs.py`:
   - `COMPANY_NAME` and `EMAIL` are identifiers sent to the SEC with requests
   - The placeholder values work fine for testing
   - For production use, you may want to use your actual email

## Usage

Run the script to download 10 PDFs from various US public companies:

```bash
python download_10k_pdfs.py
```

The script will:
1. Download 10-K filings from 10 different companies (AAPL, MSFT, GOOGL, etc.)
2. Locate the primary HTML document in each filing
3. Convert each HTML file to PDF
4. Save PDFs in the `pdfs/` directory

## Output

PDFs will be saved in the `pdfs/` directory with naming format:
```
{TICKER}_{CompanyName}_10K_{YEAR}.pdf
```

Example: `AAPL_Apple_10K_2023.pdf`

## How It Works

### Phase 1: Download (sec-edgar-downloader)
- Uses the `sec-edgar-downloader` library to handle SEC EDGAR's complex directory structures
- Automatically sets proper User-Agent headers required by the SEC
- Downloads filings to `sec-edgar-filings/` directory

### Phase 2: Locate Primary Document
- Scans the filing directory for HTML files
- Identifies the primary document (usually the first .htm file, excluding cover/graphic files)

### Phase 3: Convert to PDF (playwright)
- Uses `playwright` with a headless Chromium browser to convert HTML to PDF
- Provides accurate rendering of HTML/CSS, similar to browser "Print to PDF"
- Handles complex financial tables and formatting well
- Requires browser binaries (installed via `playwright install chromium`)

## Configuration

You can modify the script to:
- Change the list of companies: Edit `COMPANY_TICKERS` list
- Adjust number of PDFs: Change `NUM_PDFS_TO_GET`
- Update identification info: Modify `COMPANY_NAME` and `EMAIL` (optional - placeholders work fine)

## Troubleshooting

### PDF conversion fails
- Some HTML files may have complex formatting that doesn't convert perfectly
- The script will continue processing other files even if one fails

### Rate limiting
- The SEC may rate limit requests if you make too many too quickly
- The script processes one filing per company to minimize this risk

## Alternative: HTML-Only Approach

If you prefer to work with HTML files directly (which are often better for LLM extraction), you can skip the PDF conversion step. The HTML files are available in the `sec-edgar-filings/` directory structure.

## License

This project is for educational and research purposes. Ensure compliance with SEC EDGAR's terms of use.

