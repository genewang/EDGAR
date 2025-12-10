#!/usr/bin/env python3
"""
10-K Report Data Extraction and Evaluation System

This script implements both baseline (naive text chunking) and refined 
(Markdown parsing) approaches for extracting financial metrics from 10-K PDFs.
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

import pandas as pd
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LlamaIndex imports
from llama_index.core import VectorStoreIndex, Settings, Document
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

# LlamaParse for advanced PDF parsing
try:
    from llama_parse import LlamaParse
    LLAMA_PARSE_AVAILABLE = True
except ImportError:
    LLAMA_PARSE_AVAILABLE = False
    print("Warning: llama-parse not available. Install with: pip install llama-parse")

# PyPDF for baseline approach
try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    print("Warning: pypdf not available. Install with: pip install pypdf")


# ============================================================================
# Data Models
# ============================================================================

class FinancialMetrics(BaseModel):
    """Structured financial metrics extracted from 10-K reports."""
    
    company_ticker: str = Field(..., description="Company ticker symbol")
    fiscal_year: Optional[int] = Field(None, description="Fiscal year of the report")
    
    north_america_revenue: Optional[float] = Field(
        None, 
        description="Revenue attributed to North America region (in millions USD)"
    )
    
    depreciation_amortization: Optional[float] = Field(
        None,
        description="Total depreciation and amortization from Cash Flow Statement (in millions USD)"
    )
    
    lease_liabilities: Optional[float] = Field(
        None,
        description="Sum of current and non-current lease liabilities from Balance Sheet (in millions USD)"
    )
    
    @field_validator('north_america_revenue', 'depreciation_amortization', 'lease_liabilities', mode='before')
    @classmethod
    def validate_numeric(cls, v):
        """Convert string numbers to float, handle None."""
        if v is None or v == "":
            return None
        if isinstance(v, str):
            # Remove commas, dollar signs, and other formatting
            v = v.replace(',', '').replace('$', '').replace('(', '-').replace(')', '').strip()
            if v == '' or v == '-':
                return None
            try:
                return float(v)
            except ValueError:
                return None
        return float(v) if v is not None else None
    
    class Config:
        json_schema_extra = {
            "example": {
                "company_ticker": "AAPL",
                "fiscal_year": 2023,
                "north_america_revenue": 167814.0,
                "depreciation_amortization": 11104.0,
                "lease_liabilities": 11129.0
            }
        }


# ============================================================================
# Baseline Extraction (Naive Text Chunking)
# ============================================================================

class BaselineExtractor:
    """Baseline extraction using simple text chunking - expects low accuracy on tables."""
    
    def __init__(self, openai_api_key: str):
        """Initialize the baseline extractor."""
        self.llm = OpenAI(api_key=openai_api_key, model="gpt-4o", temperature=0)
        self.embed_model = OpenAIEmbedding(api_key=openai_api_key)
        Settings.llm = self.llm
        Settings.embed_model = self.embed_model
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract raw text from PDF using PyPDF."""
        if not PYPDF_AVAILABLE:
            raise ImportError("pypdf is required for baseline extraction")
        
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    def extract(self, pdf_path: Path, ticker: str) -> FinancialMetrics:
        """Extract financial metrics using baseline approach."""
        print(f"  [Baseline] Extracting text from PDF...")
        
        # Extract raw text
        text = self.extract_text_from_pdf(pdf_path)
        
        # Create documents with chunking
        documents = [Document(text=chunk) for chunk in self._chunk_text(text, chunk_size=1024)]
        
        # Create vector index
        print(f"  [Baseline] Creating vector index...")
        index = VectorStoreIndex.from_documents(documents)
        
        # Create query engine
        query_engine = index.as_query_engine(
            output_cls=FinancialMetrics,
            similarity_top_k=5
        )
        
        # Extract metrics
        print(f"  [Baseline] Querying LLM for financial metrics...")
        query = """
        Extract the following financial metrics for the most recent fiscal year:
        1. North America Revenue (or US Revenue) - from Segment Information or Geographic Revenue tables
        2. Depreciation and Amortization - from Cash Flow Statement
        3. Total Lease Liabilities (sum of current and non-current) - from Balance Sheet
        
        Return the values in millions of USD. If a value cannot be found, set it to None.
        """
        
        response = query_engine.query(query)
        
        # Parse response - LlamaIndex with output_cls returns the Pydantic model directly
        if isinstance(response, FinancialMetrics):
            metrics = response
        elif hasattr(response, 'response'):
            # Sometimes wrapped in a response object
            if isinstance(response.response, FinancialMetrics):
                metrics = response.response
            else:
                # Try to parse from dict or string
                try:
                    if isinstance(response.response, dict):
                        metrics = FinancialMetrics(**response.response)
                    elif isinstance(response.response, str):
                        import json
                        data = json.loads(response.response)
                        metrics = FinancialMetrics(**data)
                    else:
                        metrics = FinancialMetrics(company_ticker=ticker)
                except:
                    metrics = FinancialMetrics(company_ticker=ticker)
        elif isinstance(response, dict):
            metrics = FinancialMetrics(**response)
        else:
            # Fallback: create empty metrics
            metrics = FinancialMetrics(company_ticker=ticker)
        
        # Ensure ticker is set
        metrics.company_ticker = ticker
        
        return metrics
    
    def _chunk_text(self, text: str, chunk_size: int = 1024) -> list:
        """Simple text chunking by character count."""
        chunks = []
        words = text.split()
        current_chunk = []
        current_size = 0
        
        for word in words:
            word_size = len(word) + 1  # +1 for space
            if current_size + word_size > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_size = word_size
            else:
                current_chunk.append(word)
                current_size += word_size
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks


# ============================================================================
# Refined Extraction (LlamaParse + Markdown)
# ============================================================================

class RefinedExtractor:
    """Refined extraction using LlamaParse for table-preserving Markdown parsing."""
    
    def __init__(self, openai_api_key: str, llama_cloud_api_key: Optional[str] = None):
        """Initialize the refined extractor."""
        self.llm = OpenAI(api_key=openai_api_key, model="gpt-4o", temperature=0)
        self.embed_model = OpenAIEmbedding(api_key=openai_api_key)
        Settings.llm = self.llm
        Settings.embed_model = self.embed_model
        
        # Initialize LlamaParse if available
        if LLAMA_PARSE_AVAILABLE and llama_cloud_api_key:
            self.parser = LlamaParse(
                api_key=llama_cloud_api_key,
                result_type="markdown",  # Markdown preserves table structure!
                verbose=True
            )
        else:
            self.parser = None
            if not LLAMA_PARSE_AVAILABLE:
                print("  Warning: llama-parse not installed. Install with: pip install llama-parse")
            if not llama_cloud_api_key:
                print("  Warning: LLAMA_CLOUD_API_KEY not set. LlamaParse will not be used.")
    
    def extract(self, pdf_path: Path, ticker: str) -> FinancialMetrics:
        """Extract financial metrics using refined approach."""
        print(f"  [Refined] Parsing PDF with LlamaParse...")
        
        if not self.parser:
            print("  [Refined] Falling back to baseline text extraction (LlamaParse not available)")
            baseline = BaselineExtractor(os.getenv("OPENAI_API_KEY"))
            return baseline.extract(pdf_path, ticker)
        
        # Parse PDF to Markdown (preserves tables!)
        documents = self.parser.load_data(str(pdf_path))
        
        # Filter for relevant sections (Item 7, Item 8)
        filtered_docs = self._filter_relevant_sections(documents)
        
        if not filtered_docs:
            filtered_docs = documents  # Fallback to all documents
        
        # Create vector index
        print(f"  [Refined] Creating vector index from {len(filtered_docs)} documents...")
        index = VectorStoreIndex.from_documents(filtered_docs)
        
        # Create query engine with structured output
        query_engine = index.as_query_engine(
            output_cls=FinancialMetrics,
            similarity_top_k=10,
            response_mode="compact"
        )
        
        # Extract metrics with specific queries
        print(f"  [Refined] Querying LLM for financial metrics...")
        
        query = """
        Extract the following financial metrics for the most recent fiscal year from the 10-K report:
        
        1. **North America Revenue** (or US Revenue): 
           - Look in Segment Information tables (Item 1, Item 7, or Item 8)
           - Find revenue attributed to North America or United States region
           - Value should be in millions of USD
        
        2. **Depreciation and Amortization**:
           - Look in the Statement of Cash Flows (Item 8)
           - Find the line item for "Depreciation and amortization" or "Depreciation and amortization expense"
           - Value should be in millions of USD
        
        3. **Total Lease Liabilities**:
           - Look in the Balance Sheet (Item 8)
           - Find "Lease liabilities" or "Operating lease liabilities"
           - If split between "Current" and "Non-current", sum them
           - If a "Total" line exists, use that
           - Value should be in millions of USD
        
        Pay special attention to:
        - Table structure (rows and columns)
        - Fiscal year labels (ensure you get the most recent year)
        - Units (convert to millions if needed)
        - Negative numbers (may be in parentheses)
        
        If a value cannot be found, set it to None.
        """
        
        response = query_engine.query(query)
        
        # Parse response - LlamaIndex with output_cls returns the Pydantic model directly
        if isinstance(response, FinancialMetrics):
            metrics = response
        elif hasattr(response, 'response'):
            # Sometimes wrapped in a response object
            if isinstance(response.response, FinancialMetrics):
                metrics = response.response
            else:
                # Try to parse from dict or string
                try:
                    if isinstance(response.response, dict):
                        metrics = FinancialMetrics(**response.response)
                    elif isinstance(response.response, str):
                        import json
                        data = json.loads(response.response)
                        metrics = FinancialMetrics(**data)
                    else:
                        metrics = FinancialMetrics(company_ticker=ticker)
                except:
                    metrics = FinancialMetrics(company_ticker=ticker)
        elif isinstance(response, dict):
            metrics = FinancialMetrics(**response)
        else:
            # Fallback: create empty metrics
            metrics = FinancialMetrics(company_ticker=ticker)
        
        # Ensure ticker is set
        metrics.company_ticker = ticker
        
        return metrics
    
    def _filter_relevant_sections(self, documents: list) -> list:
        """Filter documents to focus on Item 7 and Item 8 (Financial Statements)."""
        relevant_keywords = [
            "item 7", "item 8", "financial statements", 
            "consolidated statements", "segment information",
            "balance sheet", "income statement", "cash flow"
        ]
        
        filtered = []
        for doc in documents:
            text_lower = doc.text.lower()
            if any(keyword in text_lower for keyword in relevant_keywords):
                filtered.append(doc)
        
        return filtered


# ============================================================================
# Evaluation Framework
# ============================================================================

class Evaluator:
    """Evaluate extraction results against ground truth."""
    
    def __init__(self, ground_truth_path: Path):
        """Initialize evaluator with ground truth data."""
        self.ground_truth = pd.read_csv(ground_truth_path)
        self.ground_truth.set_index('ticker', inplace=True)
    
    def evaluate(self, extracted: FinancialMetrics, tolerance: float = 0.01) -> Dict[str, Any]:
        """Evaluate extracted metrics against ground truth."""
        ticker = extracted.company_ticker
        
        if ticker not in self.ground_truth.index:
            return {
                'ticker': ticker,
                'error': f'Ticker {ticker} not found in ground truth'
            }
        
        gt = self.ground_truth.loc[ticker]
        
        results = {
            'ticker': ticker,
            'metrics': {}
        }
        
        # Evaluate each metric
        for metric in ['north_america_revenue', 'depreciation_amortization', 'lease_liabilities']:
            extracted_val = getattr(extracted, metric)
            gt_val = gt.get(metric)
            
            if pd.isna(gt_val) or gt_val is None:
                results['metrics'][metric] = {
                    'extracted': extracted_val,
                    'ground_truth': None,
                    'match': None,
                    'error': 'No ground truth available'
                }
                continue
            
            if extracted_val is None:
                results['metrics'][metric] = {
                    'extracted': None,
                    'ground_truth': float(gt_val),
                    'match': False,
                    'error': 'Value not extracted'
                }
                continue
            
            # Check if values match within tolerance
            diff = abs(extracted_val - float(gt_val))
            relative_error = diff / abs(float(gt_val)) if float(gt_val) != 0 else float('inf')
            match = relative_error <= tolerance
            
            results['metrics'][metric] = {
                'extracted': extracted_val,
                'ground_truth': float(gt_val),
                'match': match,
                'absolute_error': diff,
                'relative_error': relative_error,
                'error_type': self._classify_error(extracted_val, float(gt_val), relative_error)
            }
        
        # Calculate overall accuracy
        matches = sum(1 for m in results['metrics'].values() if m.get('match') is True)
        total = sum(1 for m in results['metrics'].values() if m.get('ground_truth') is not None)
        results['accuracy'] = matches / total if total > 0 else 0.0
        
        return results
    
    def _classify_error(self, extracted: float, ground_truth: float, relative_error: float) -> str:
        """Classify the type of error."""
        if relative_error <= 0.01:
            return "None (within tolerance)"
        elif relative_error <= 0.10:
            return "Minor (rounding/formatting)"
        elif abs(extracted - ground_truth) / abs(ground_truth) > 0.50:
            return "Major (wrong value/column)"
        else:
            return "Moderate (partial match)"


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract financial metrics from 10-K PDFs')
    parser.add_argument('--mode', choices=['baseline', 'refined', 'both'], default='both',
                       help='Extraction mode: baseline, refined, or both')
    parser.add_argument('--pdf-dir', type=str, default='pdfs',
                       help='Directory containing PDF files')
    parser.add_argument('--ground-truth', type=str, default='ground_truth.csv',
                       help='Path to ground truth CSV file')
    parser.add_argument('--output', type=str, default='extraction_results.json',
                       help='Output file for extraction results')
    parser.add_argument('--evaluate', action='store_true',
                       help='Evaluate results against ground truth')
    
    args = parser.parse_args()
    
    # Check for API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("Error: OPENAI_API_KEY not found in environment variables.")
        print("Please set it in a .env file or export it.")
        sys.exit(1)
    
    llama_key = os.getenv("LLAMA_CLOUD_API_KEY")
    if args.mode in ['refined', 'both'] and not llama_key:
        print("Warning: LLAMA_CLOUD_API_KEY not found. Refined extraction may fall back to baseline.")
    
    # Get PDF files
    pdf_dir = Path(args.pdf_dir)
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"Error: No PDF files found in {pdf_dir}")
        sys.exit(1)
    
    print(f"Found {len(pdf_files)} PDF files to process")
    print("=" * 60)
    
    results = {}
    
    # Process each PDF
    for pdf_path in pdf_files:
        # Extract ticker from filename (e.g., AAPL_Apple_10K_0000.pdf -> AAPL)
        ticker = pdf_path.stem.split('_')[0]
        print(f"\nProcessing {ticker}: {pdf_path.name}")
        
        results[ticker] = {}
        
        # Baseline extraction
        if args.mode in ['baseline', 'both']:
            try:
                print(f"  Running baseline extraction...")
                baseline_extractor = BaselineExtractor(openai_key)
                baseline_result = baseline_extractor.extract(pdf_path, ticker)
                results[ticker]['baseline'] = baseline_result.model_dump()
                print(f"  ✓ Baseline extraction complete")
            except Exception as e:
                print(f"  ✗ Baseline extraction failed: {e}")
                results[ticker]['baseline'] = {'error': str(e)}
        
        # Refined extraction
        if args.mode in ['refined', 'both']:
            try:
                print(f"  Running refined extraction...")
                refined_extractor = RefinedExtractor(openai_key, llama_key)
                refined_result = refined_extractor.extract(pdf_path, ticker)
                results[ticker]['refined'] = refined_result.model_dump()
                print(f"  ✓ Refined extraction complete")
            except Exception as e:
                print(f"  ✗ Refined extraction failed: {e}")
                import traceback
                traceback.print_exc()
                results[ticker]['refined'] = {'error': str(e)}
    
    # Save results
    output_path = Path(args.output)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n{'=' * 60}")
    print(f"Results saved to {output_path}")
    
    # Evaluate if requested
    if args.evaluate:
        ground_truth_path = Path(args.ground_truth)
        if not ground_truth_path.exists():
            print(f"\nWarning: Ground truth file {ground_truth_path} not found. Skipping evaluation.")
            print("Create a ground_truth.csv file with columns: ticker, north_america_revenue, depreciation_amortization, lease_liabilities")
        else:
            print(f"\n{'=' * 60}")
            print("Evaluating results against ground truth...")
            evaluator = Evaluator(ground_truth_path)
            
            evaluation_results = {}
            for ticker, ticker_results in results.items():
                evaluation_results[ticker] = {}
                
                if 'baseline' in ticker_results and 'error' not in ticker_results['baseline']:
                    baseline_metrics = FinancialMetrics(**ticker_results['baseline'])
                    evaluation_results[ticker]['baseline'] = evaluator.evaluate(baseline_metrics)
                
                if 'refined' in ticker_results and 'error' not in ticker_results['refined']:
                    refined_metrics = FinancialMetrics(**ticker_results['refined'])
                    evaluation_results[ticker]['refined'] = evaluator.evaluate(refined_metrics)
            
            # Generate summary report
            print("\n" + "=" * 60)
            print("EVALUATION SUMMARY")
            print("=" * 60)
            
            for ticker, eval_results in evaluation_results.items():
                print(f"\n{ticker}:")
                for method in ['baseline', 'refined']:
                    if method in eval_results:
                        acc = eval_results[method].get('accuracy', 0)
                        print(f"  {method.capitalize()}: {acc:.1%} accuracy")
                        for metric, details in eval_results[method].get('metrics', {}).items():
                            if details.get('match') is not None:
                                status = "✓" if details['match'] else "✗"
                                print(f"    {status} {metric}: {details.get('extracted')} vs {details.get('ground_truth')}")
            
            # Save evaluation results
            eval_output = output_path.parent / f"evaluation_{output_path.stem}.json"
            with open(eval_output, 'w') as f:
                json.dump(evaluation_results, f, indent=2, default=str)
            print(f"\nEvaluation results saved to {eval_output}")


if __name__ == "__main__":
    main()

