#!/usr/bin/env python3
"""
10-K Report Data Extraction and Evaluation System

This script implements both baseline (naive text chunking) and refined 
(Markdown parsing) approaches for extracting financial metrics from 10-K PDFs.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

import pandas as pd
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ollama_debug.log')
    ]
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# LlamaIndex imports
from llama_index.core import VectorStoreIndex, Settings, Document
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.embeddings import BaseEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

# Ollama support (optional)
try:
    from llama_index.llms.ollama import Ollama
    import requests
    try:
        import ollama
        OLLAMA_PYTHON_AVAILABLE = True
    except ImportError:
        OLLAMA_PYTHON_AVAILABLE = False
    OLLAMA_AVAILABLE = True
    # Try to import Ollama embeddings (may not be available)
    try:
        from llama_index.embeddings.ollama import OllamaEmbedding
        OLLAMA_EMBEDDINGS_AVAILABLE = True
    except ImportError:
        OLLAMA_EMBEDDINGS_AVAILABLE = False
        # We'll create a custom embedding class using Ollama API
except ImportError:
    OLLAMA_AVAILABLE = False
    OLLAMA_EMBEDDINGS_AVAILABLE = False
    print("Warning: llama-index-llms-ollama not available. Install with: pip install llama-index-llms-ollama")

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

# BeautifulSoup for HTML parsing
try:
    from bs4 import BeautifulSoup
    HTML_PARSING_AVAILABLE = True
except ImportError:
    HTML_PARSING_AVAILABLE = False
    print("Warning: beautifulsoup4 not available. Install with: pip install beautifulsoup4 lxml")


# ============================================================================
# Data Models
# ============================================================================

class FinancialMetrics(BaseModel):
    """Structured financial metrics extracted from 10-K reports."""
    
    company_ticker: str = Field(..., description="Company ticker symbol")
    fiscal_year: Optional[int] = Field(None, description="Fiscal year of the report")
    
    cik: Optional[str] = Field(
        None, 
        description="Central Index Key (CIK) - company identifier from SEC filings"
    )
    
    total_revenue: Optional[float] = Field(
        None,
        description="Total revenue from Income Statement (in millions USD)"
    )
    
    net_income: Optional[float] = Field(
        None,
        description="Net income from Income Statement (in millions USD)"
    )
    
    @field_validator('total_revenue', 'net_income', mode='before')
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
    
    @field_validator('cik', mode='before')
    @classmethod
    def validate_cik(cls, v):
        """Validate and format CIK."""
        if v is None or v == "":
            return None
        if isinstance(v, (int, float)):
            # Convert to string and pad with leading zeros if needed
            cik_str = str(int(v))
            # CIK is typically 10 digits, pad with leading zeros
            return cik_str.zfill(10)
        if isinstance(v, str):
            # Remove any formatting and pad with leading zeros
            cik_clean = v.replace('-', '').replace(' ', '').strip()
            if cik_clean == '':
                return None
            try:
                # Validate it's numeric
                cik_int = int(cik_clean)
                return str(cik_int).zfill(10)
            except ValueError:
                return v.strip()  # Return as-is if not numeric
        return str(v) if v is not None else None
    
    class Config:
        json_schema_extra = {
            "example": {
                "company_ticker": "AAPL",
                "fiscal_year": 2023,
                "cik": "0000320193",
                "total_revenue": 383285.0,
                "net_income": 96995.0
            }
        }


# ============================================================================
# Custom Ollama Embedding Class
# ============================================================================

class OllamaEmbeddingCustom(BaseEmbedding):
    """Custom embedding class that uses Ollama's embedding API directly."""
    
    model_name: str = "nomic-embed-text"
    base_url: str = "http://localhost:11434"
    
    def __init__(self, model_name: str = "nomic-embed-text", base_url: str = "http://localhost:11434", **kwargs):
        super().__init__(model_name=model_name, base_url=base_url.rstrip('/'), **kwargs)
        self._embed_dim = None
    
    def _get_query_embedding(self, query: str) -> list:
        """Get embedding for a query."""
        return self._get_text_embedding(query)
    
    async def _aget_query_embedding(self, query: str) -> list:
        """Get embedding for a query (async)."""
        return await self._aget_text_embedding(query)
    
    def _get_text_embedding(self, text: str) -> list:
        """Get embedding for a single text."""
        logger.debug(f"Getting embedding for text (length: {len(text)}) using model: {self.model_name}")
        
        # Try using ollama Python library first (more reliable)
        if OLLAMA_PYTHON_AVAILABLE:
            try:
                logger.debug(f"Using ollama Python library for embeddings")
                result = ollama.embeddings(model=self.model_name, prompt=text)
                embedding = result.get("embedding", [])
                logger.debug(f"Got embedding of dimension: {len(embedding)}")
                if self._embed_dim is None:
                    self._embed_dim = len(embedding)
                    logger.info(f"Embedding dimension set to: {self._embed_dim}")
                return embedding
            except Exception as e:
                logger.warning(f"Ollama Python library failed: {e}, falling back to HTTP requests")
                # Fall back to HTTP requests
                pass
        
        # Fall back to HTTP requests
        logger.debug("Using HTTP requests for embeddings")
        try:
            # Try OpenAI-compatible endpoint
            logger.debug(f"Trying OpenAI-compatible endpoint: {self.base_url}/v1/embeddings")
            response = requests.post(
                f"{self.base_url}/v1/embeddings",
                json={"model": self.model_name, "input": text},
                timeout=30
            )
            logger.debug(f"Response status: {response.status_code}")
            response.raise_for_status()
            result = response.json()
            embedding = result.get("data", [{}])[0].get("embedding", [])
            logger.debug(f"Got embedding of dimension: {len(embedding)} from OpenAI-compatible endpoint")
        except Exception as e:
            logger.warning(f"OpenAI-compatible endpoint failed: {e}, trying native endpoint")
            # Try native Ollama endpoint
            try:
                logger.debug(f"Trying native Ollama endpoint: {self.base_url}/api/embeddings")
                response = requests.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.model_name, "prompt": text},
                    timeout=30
                )
                logger.debug(f"Response status: {response.status_code}")
                response.raise_for_status()
                result = response.json()
                embedding = result.get("embedding", [])
                logger.debug(f"Got embedding of dimension: {len(embedding)} from native endpoint")
            except Exception as e2:
                logger.error(f"All embedding endpoints failed. Last error: {e2}", exc_info=True)
                raise
        
        if self._embed_dim is None:
            self._embed_dim = len(embedding)
            logger.info(f"Embedding dimension set to: {self._embed_dim}")
        return embedding
    
    async def _aget_text_embedding(self, text: str) -> list:
        """Get embedding for a single text (async)."""
        # For simplicity, use sync version (can be improved with aiohttp)
        return self._get_text_embedding(text)
    
    def _get_text_embeddings(self, texts: list) -> list:
        """Get embeddings for multiple texts."""
        return [self._get_text_embedding(text) for text in texts]
    
    async def _aget_text_embeddings(self, texts: list) -> list:
        """Get embeddings for multiple texts (async)."""
        return [await self._aget_text_embedding(text) for text in texts]
    
    @property
    def embed_dim(self) -> int:
        """Get the embedding dimension."""
        if self._embed_dim is None:
            # Initialize by getting an embedding for a dummy text
            self._get_text_embedding("test")
        return self._embed_dim


# ============================================================================
# Model Configuration Helper
# ============================================================================

def _initialize_models(use_ollama: bool = False, ollama_model: str = "gpt-oss:20b", 
                       ollama_base_url: str = "http://localhost:11434",
                       openai_api_key: Optional[str] = None):
    """
    Initialize LLM and embedding models based on configuration.
    
    Args:
        use_ollama: If True, use local Ollama server; if False, use OpenAI
        ollama_model: Model name for Ollama (default: "gpt-oss:20b")
        ollama_base_url: Base URL for Ollama server (default: "http://localhost:11434")
        openai_api_key: OpenAI API key (required if use_ollama=False)
    
    Returns:
        Tuple of (llm, embed_model)
    """
    if use_ollama:
        if not OLLAMA_AVAILABLE:
            raise ImportError(
                "Ollama support requested but llama-index-llms-ollama is not installed. "
                "Install with: pip install llama-index-llms-ollama"
            )
        
        logger.info(f"Initializing Ollama LLM: model={ollama_model}, base_url={ollama_base_url}")
        print(f"  [Config] Using Ollama model: {ollama_model} at {ollama_base_url}")
        
        # Check Ollama server status
        try:
            if OLLAMA_PYTHON_AVAILABLE:
                logger.debug("Checking Ollama server status using Python library...")
                models = ollama.list()
                logger.debug(f"Available Ollama models: {[m['name'] for m in models.get('models', [])]}")
                if not any(m['name'] == ollama_model for m in models.get('models', [])):
                    logger.warning(f"Model {ollama_model} not found in Ollama. Available models: {[m['name'] for m in models.get('models', [])]}")
        except Exception as e:
            logger.warning(f"Could not check Ollama models: {e}")
        
        # Check system memory
        try:
            import psutil
            mem = psutil.virtual_memory()
            logger.info(f"System memory - Total: {mem.total / (1024**3):.2f} GB, Available: {mem.available / (1024**3):.2f} GB, Used: {mem.used / (1024**3):.2f} GB")
            print(f"  [Debug] System memory - Available: {mem.available / (1024**3):.2f} GB / Total: {mem.total / (1024**3):.2f} GB")
        except ImportError:
            logger.warning("psutil not available for memory checking. Install with: pip install psutil")
        except Exception as e:
            logger.warning(f"Could not check system memory: {e}")
        
        logger.debug(f"Creating Ollama LLM instance with timeout=120.0, temperature=0.1")
        llm = Ollama(
            model=ollama_model,
            base_url=ollama_base_url,
            temperature=0.1,
            request_timeout=120.0  # Longer timeout for local models
        )
        logger.debug("Ollama LLM instance created successfully")
        # Use Ollama embeddings - try official package first, then custom implementation
        embed_model = None
        if OLLAMA_EMBEDDINGS_AVAILABLE:
            try:
                embed_model = OllamaEmbedding(
                    model_name=ollama_model,
                    base_url=ollama_base_url
                )
                print(f"  [Config] Using Ollama embeddings (official): {ollama_model}")
            except Exception as e:
                print(f"  [Config] Warning: Could not initialize official Ollama embeddings: {e}")
                embed_model = None
        
        # Fall back to custom Ollama embedding implementation
        if embed_model is None:
            try:
                logger.debug("Initializing custom Ollama embeddings with nomic-embed-text")
                # Try using nomic-embed-text (common embedding model)
                embed_model = OllamaEmbeddingCustom(
                    model_name="nomic-embed-text",
                    base_url=ollama_base_url
                )
                logger.info("Custom Ollama embeddings initialized successfully")
                print(f"  [Config] Using Ollama embeddings (custom): nomic-embed-text")
            except Exception as e:
                logger.error(f"Failed to initialize Ollama embeddings: {e}", exc_info=True)
                print(f"  [Config] Warning: Could not initialize Ollama embeddings: {e}")
                print(f"  [Config] Falling back to OpenAI embeddings")
                if not openai_api_key:
                    raise ValueError(
                        "OpenAI API key required for embeddings when Ollama embeddings unavailable. "
                        "Make sure Ollama server is running and 'nomic-embed-text' model is available: "
                        "ollama pull nomic-embed-text"
                    )
                logger.info("Falling back to OpenAI embeddings")
                embed_model = OpenAIEmbedding(api_key=openai_api_key)
    else:
        if not openai_api_key:
            raise ValueError("OpenAI API key required when not using Ollama")
        print(f"  [Config] Using OpenAI model: gpt-4o")
        llm = OpenAI(api_key=openai_api_key, model="gpt-4o", temperature=0)
        embed_model = OpenAIEmbedding(api_key=openai_api_key)
    
    return llm, embed_model


# ============================================================================
# Baseline Extraction (Naive Text Chunking)
# ============================================================================

class BaselineExtractor:
    """Baseline extraction using simple text chunking - expects low accuracy on tables."""
    
    def __init__(self, openai_api_key: Optional[str] = None, 
                 use_ollama: bool = False,
                 ollama_model: str = "gpt-oss:20b",
                 ollama_base_url: str = "http://localhost:11434"):
        """
        Initialize the baseline extractor.
        
        Args:
            openai_api_key: OpenAI API key (required if use_ollama=False)
            use_ollama: If True, use local Ollama server instead of OpenAI
            ollama_model: Model name for Ollama (default: "gpt-oss:20b")
            ollama_base_url: Base URL for Ollama server (default: "http://localhost:11434")
        """
        self.llm, self.embed_model = _initialize_models(
            use_ollama=use_ollama,
            ollama_model=ollama_model,
            ollama_base_url=ollama_base_url,
            openai_api_key=openai_api_key
        )
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
    
    def extract_text_from_html(self, html_path: Path) -> str:
        """Extract text from HTML file, preserving table structure."""
        if not HTML_PARSING_AVAILABLE:
            raise ImportError("beautifulsoup4 is required for HTML extraction")
        
        logger.debug(f"Extracting text from HTML: {html_path}")
        
        with open(html_path, 'r', encoding='utf-8', errors='ignore') as file:
            html_content = file.read()
        
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Extract text, preserving table structure
        text_parts = []
        
        # Process tables separately to preserve structure
        for table in soup.find_all('table'):
            table_text = []
            for row in table.find_all('tr'):
                cells = []
                for cell in row.find_all(['td', 'th']):
                    cell_text = cell.get_text(strip=True, separator=' ')
                    cells.append(cell_text)
                if cells:
                    table_text.append(' | '.join(cells))
            if table_text:
                text_parts.append('\n'.join(table_text))
                text_parts.append('\n')  # Separator between tables
        
        # Extract non-table text
        for element in soup.find_all(['p', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            if element.name != 'table' and element.find_parent('table') is None:
                text = element.get_text(strip=True, separator=' ')
                if text:
                    text_parts.append(text)
        
        # Fallback: get all text if no structured extraction worked
        if not text_parts:
            text_parts.append(soup.get_text(separator=' ', strip=True))
        
        return '\n'.join(text_parts)
    
    def extract(self, file_path: Path, ticker: str, file_type: str = "pdf") -> FinancialMetrics:
        """
        Extract financial metrics using baseline approach.
        
        Args:
            file_path: Path to PDF or HTML file
            ticker: Company ticker symbol
            file_type: "pdf" or "html"
        """
        if file_type.lower() == "html":
            print(f"  [Baseline] Extracting text from HTML...")
            text = self.extract_text_from_html(file_path)
        else:
            print(f"  [Baseline] Extracting text from PDF...")
            text = self.extract_text_from_pdf(file_path)
        
        # Create documents with chunking
        documents = [Document(text=chunk) for chunk in self._chunk_text(text, chunk_size=1024)]
        
        # Create vector index
        print(f"  [Baseline] Creating vector index...")
        index = VectorStoreIndex.from_documents(documents)
        
        # Create query engine
        logger.debug("Creating query engine with output_cls=FinancialMetrics, similarity_top_k=5")
        query_engine = index.as_query_engine(
            output_cls=FinancialMetrics,
            similarity_top_k=5
        )
        logger.debug("Query engine created successfully")
        
        # Extract metrics
        print(f"  [Baseline] Querying LLM for financial metrics...")
        query = """
        Extract the following financial metrics for the most recent fiscal year:
        1. CIK (Central Index Key) - company identifier, typically found in the header or cover page of the 10-K filing
        2. Total Revenue - from the Income Statement (Statement of Operations), look for "Total revenue", "Net sales", or "Revenue"
        3. Net Income - from the Income Statement, look for "Net income", "Net earnings", or "Net income (loss)"
        
        Return the values in millions of USD (except CIK which is a string identifier). If a value cannot be found, set it to None.
        """
        
        logger.info(f"Querying LLM with query length: {len(query)}")
        logger.debug(f"Query content: {query[:200]}...")
        try:
            logger.debug("Calling query_engine.query()...")
            response = query_engine.query(query)
            logger.info("LLM query completed successfully")
            logger.debug(f"Response type: {type(response)}")
        except Exception as e:
            logger.error(f"LLM query failed: {e}", exc_info=True)
            # Check if it's a memory issue
            error_str = str(e).lower()
            if "memory" in error_str or "14.8" in error_str:
                logger.error("Memory error detected. Checking current memory status...")
                try:
                    import psutil
                    mem = psutil.virtual_memory()
                    logger.error(f"Current memory - Available: {mem.available / (1024**3):.2f} GB, Used: {mem.used / (1024**3):.2f} GB")
                    logger.error(f"Memory percent used: {mem.percent}%")
                except:
                    pass
            raise
        
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
    
    def __init__(self, openai_api_key: Optional[str] = None, 
                 llama_cloud_api_key: Optional[str] = None,
                 use_ollama: bool = False,
                 ollama_model: str = "gpt-oss:20b",
                 ollama_base_url: str = "http://localhost:11434"):
        """
        Initialize the refined extractor.
        
        Args:
            openai_api_key: OpenAI API key (required if use_ollama=False)
            llama_cloud_api_key: LlamaCloud API key for LlamaParse
            use_ollama: If True, use local Ollama server instead of OpenAI
            ollama_model: Model name for Ollama (default: "gpt-oss:20b")
            ollama_base_url: Base URL for Ollama server (default: "http://localhost:11434")
        """
        self.llm, self.embed_model = _initialize_models(
            use_ollama=use_ollama,
            ollama_model=ollama_model,
            ollama_base_url=ollama_base_url,
            openai_api_key=openai_api_key
        )
        Settings.llm = self.llm
        Settings.embed_model = self.embed_model
        
        # Store configuration for fallback
        self._use_ollama = use_ollama
        self._ollama_model = ollama_model
        self._ollama_base_url = ollama_base_url
        
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
            # Use the same configuration as this extractor
            use_ollama = hasattr(self, '_use_ollama') and self._use_ollama
            baseline = BaselineExtractor(
                openai_api_key=os.getenv("OPENAI_API_KEY") if not use_ollama else None,
                use_ollama=use_ollama,
                ollama_model=getattr(self, '_ollama_model', "gpt-oss:20b"),
                ollama_base_url=getattr(self, '_ollama_base_url', "http://localhost:11434")
            )
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
        
        1. **CIK (Central Index Key)**:
           - Look in the cover page or header of the 10-K filing
           - Find "Commission File Number" or "CIK" or "Central Index Key"
           - Format as a 10-digit string (e.g., "0000320193")
           - This is a company identifier, not a financial metric
        
        2. **Total Revenue**:
           - Look in the Income Statement (Statement of Operations) in Item 8
           - Find "Total revenue", "Net sales", "Revenue", or "Net revenue"
           - Use the most recent fiscal year column
           - Value should be in millions of USD
        
        3. **Net Income**:
           - Look in the Income Statement (Statement of Operations) in Item 8
           - Find "Net income", "Net earnings", "Net income (loss)", or "Net loss"
           - Use the most recent fiscal year column
           - Value should be in millions of USD (negative if loss)
        
        Pay special attention to:
        - Table structure (rows and columns)
        - Fiscal year labels (ensure you get the most recent year)
        - Units (convert to millions if needed)
        - Negative numbers (may be in parentheses or shown as negative)
        
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
        for metric in ['cik', 'total_revenue', 'net_income']:
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
                # For CIK, convert to string for comparison
                if metric == 'cik':
                    results['metrics'][metric] = {
                        'extracted': None,
                        'ground_truth': str(gt_val),
                        'match': False,
                        'error': 'Value not extracted'
                    }
                else:
                    results['metrics'][metric] = {
                        'extracted': None,
                        'ground_truth': float(gt_val),
                        'match': False,
                        'error': 'Value not extracted'
                    }
                continue
            
            # Special handling for CIK (string comparison)
            if metric == 'cik':
                # Normalize CIK values for comparison (remove leading zeros, dashes, etc.)
                extracted_cik = str(extracted_val).replace('-', '').replace(' ', '').strip()
                gt_cik = str(gt_val).replace('-', '').replace(' ', '').strip()
                # Pad with leading zeros to 10 digits for comparison
                extracted_cik = extracted_cik.zfill(10)
                gt_cik = gt_cik.zfill(10)
                match = extracted_cik == gt_cik
                
                results['metrics'][metric] = {
                    'extracted': extracted_val,
                    'ground_truth': str(gt_val),
                    'match': match,
                    'error_type': 'None (exact match)' if match else 'Major (wrong value)'
                }
            else:
                # Numeric comparison for revenue and net income
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
    parser.add_argument('--use-ollama', action='store_true',
                       help='Use local Ollama server instead of OpenAI')
    parser.add_argument('--ollama-model', type=str, default='gpt-oss:20b',
                       help='Ollama model name (default: gpt-oss:20b)')
    parser.add_argument('--ollama-base-url', type=str, default='http://localhost:11434',
                       help='Ollama server base URL (default: http://localhost:11434)')
    
    args = parser.parse_args()
    
    # Check for API keys and configuration
    use_ollama = args.use_ollama or os.getenv("USE_OLLAMA", "").lower() in ("true", "1", "yes")
    ollama_model = args.ollama_model or os.getenv("OLLAMA_MODEL", "gpt-oss:20b")
    ollama_base_url = args.ollama_base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not use_ollama:
        if not openai_key:
            print("Error: OPENAI_API_KEY not found in environment variables.")
            print("Please set it in a .env file or export it.")
            print("Alternatively, use --use-ollama to use a local Ollama server.")
            sys.exit(1)
    else:
        if not OLLAMA_AVAILABLE:
            print("Error: Ollama support requested but llama-index-llms-ollama is not installed.")
            print("Install with: pip install llama-index-llms-ollama")
            sys.exit(1)
        print(f"Using Ollama configuration:")
        print(f"  Model: {ollama_model}")
        print(f"  Base URL: {ollama_base_url}")
        # OpenAI key may still be needed for embeddings if Ollama embeddings fail
        if not openai_key:
            print("Warning: OPENAI_API_KEY not set. Embeddings may fall back to OpenAI if Ollama embeddings fail.")
    
    llama_key = os.getenv("LLAMA_CLOUD_API_KEY")
    if args.mode in ['refined', 'both'] and not llama_key:
        print("Warning: LLAMA_CLOUD_API_KEY not found. Refined extraction may fall back to baseline.")
    
    # Get PDF files - filter to only those in ground truth if specified
    pdf_dir = Path(args.pdf_dir)
    
    # If ground truth is specified, only process PDFs for those tickers
    ground_truth_path = Path(args.ground_truth)
    target_tickers = set()
    
    if ground_truth_path.exists():
        gt_df = pd.read_csv(ground_truth_path)
        target_tickers = set(gt_df['ticker'].str.strip().str.upper())
        print(f"Found {len(target_tickers)} companies in ground truth: {sorted(target_tickers)}")
    
    # Get all PDF files
    all_pdf_files = list(pdf_dir.glob("*.pdf"))
    
    # Filter to only PDFs for companies in ground truth
    if target_tickers:
        pdf_files = []
        for pdf_path in all_pdf_files:
            # Extract ticker from filename (e.g., AAPL_Apple_10K_0000.pdf -> AAPL)
            ticker = pdf_path.stem.split('_')[0].upper()
            if ticker in target_tickers:
                pdf_files.append(pdf_path)
            else:
                print(f"Skipping {pdf_path.name} (not in ground truth)")
        
        if not pdf_files:
            print(f"Error: No PDF files found for companies in {ground_truth_path}")
            print(f"Expected tickers: {sorted(target_tickers)}")
            sys.exit(1)
    else:
        pdf_files = all_pdf_files
    
    if not pdf_files:
        print(f"Error: No PDF files found in {pdf_dir}")
        sys.exit(1)
    
    print(f"Processing {len(pdf_files)} PDF file(s) from ground truth")
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
                baseline_extractor = BaselineExtractor(
                    openai_api_key=openai_key if not use_ollama else None,
                    use_ollama=use_ollama,
                    ollama_model=ollama_model,
                    ollama_base_url=ollama_base_url
                )
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
                refined_extractor = RefinedExtractor(
                    openai_api_key=openai_key if not use_ollama else None,
                    llama_cloud_api_key=llama_key,
                    use_ollama=use_ollama,
                    ollama_model=ollama_model,
                    ollama_base_url=ollama_base_url
                )
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
            print("Create a ground_truth.csv file with columns: ticker, cik, total_revenue, net_income")
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

