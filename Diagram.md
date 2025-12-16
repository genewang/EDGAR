# 10-K Financial Data Extraction System - Architecture & Flow Diagrams

## Table of Contents
1. [System Architecture Overview](#system-architecture-overview)
2. [Component Architecture](#component-architecture)
3. [Data Flow Diagram](#data-flow-diagram)
4. [State Diagram](#state-diagram)
5. [Sequence Diagram](#sequence-diagram)
6. [Extraction Pipeline Flow](#extraction-pipeline-flow)

---

## System Architecture Overview

```mermaid
graph TB
    subgraph "Input Layer"
        PDF[10-K PDF Files]
        HTML[10-K HTML Files]
        GT[Ground Truth CSV]
    end
    
    subgraph "Extraction Layer"
        BE[Baseline Extractor]
        RE[Refined Extractor]
    end
    
    subgraph "Processing Components"
        Parser[PDF/HTML Parser]
        Chunker[Text Chunker]
        VectorIndex[Vector Store Index]
        LLM[LLM Query Engine]
    end
    
    subgraph "External Services"
        Ollama[Ollama Server]
        OpenAI[OpenAI API]
        LlamaCloud[LlamaCloud API]
    end
    
    subgraph "Output Layer"
        Metrics[FinancialMetrics]
        Results[JSON Results]
        Eval[Evaluation Results]
    end
    
    PDF --> BE
    PDF --> RE
    HTML --> BE
    
    BE --> Parser
    BE --> Chunker
    RE --> Parser
    
    Parser --> VectorIndex
    Chunker --> VectorIndex
    VectorIndex --> LLM
    
    LLM --> Ollama
    LLM --> OpenAI
    RE --> LlamaCloud
    
    LLM --> Metrics
    Metrics --> Results
    Results --> Eval
    GT --> Eval
    
    style BE fill:#e1f5ff
    style RE fill:#fff4e1
    style LLM fill:#ffe1f5
    style Metrics fill:#e1ffe1
```

---

## Component Architecture

```mermaid
classDiagram
    class FinancialMetrics {
        +str company_ticker
        +Optional[int] fiscal_year
        +Optional[str] cik
        +Optional[float] total_revenue
        +Optional[float] net_income
        +validate_numeric()
        +validate_cik()
    }
    
    class BaselineExtractor {
        -LLM llm
        -Embedding embed_model
        +extract(file_path, ticker, file_type)
        +extract_text_from_pdf(pdf_path)
        +extract_text_from_html(html_path)
        -_chunk_text(text, chunk_size)
    }
    
    class RefinedExtractor {
        -LLM llm
        -Embedding embed_model
        -LlamaParse parser
        +extract(pdf_path, ticker)
        -_filter_relevant_sections(documents)
    }
    
    class Evaluator {
        -DataFrame ground_truth
        +evaluate(extracted, tolerance)
        -_classify_error(extracted, ground_truth, relative_error)
    }
    
    class OllamaEmbeddingCustom {
        -str model_name
        -str base_url
        +_get_text_embedding(text)
        +_get_query_embedding(query)
    }
    
    class VectorStoreIndex {
        +from_documents(documents)
        +as_query_engine(output_cls, similarity_top_k)
    }
    
    BaselineExtractor --> FinancialMetrics : produces
    RefinedExtractor --> FinancialMetrics : produces
    Evaluator --> FinancialMetrics : evaluates
    BaselineExtractor --> VectorStoreIndex : uses
    RefinedExtractor --> VectorStoreIndex : uses
    BaselineExtractor --> OllamaEmbeddingCustom : uses
    RefinedExtractor --> OllamaEmbeddingCustom : uses
```

---

## Data Flow Diagram

```mermaid
flowchart TD
    Start([Start: Input File]) --> CheckType{File Type?}
    
    CheckType -->|PDF| PDFPath[PDF File Path]
    CheckType -->|HTML| HTMLPath[HTML File Path]
    
    PDFPath --> Method{Extraction Method?}
    HTMLPath --> BaselineOnly[Baseline Only]
    
    Method -->|Baseline| BaselineFlow[Baseline Flow]
    Method -->|Refined| RefinedFlow[Refined Flow]
    Method -->|Both| BothFlow[Both Flows]
    
    BaselineOnly --> BaselineFlow
    
    subgraph BaselineFlow["Baseline Extraction Flow"]
        B1[Extract Text<br/>PyPDF/BeautifulSoup]
        B2[Chunk Text<br/>1024 tokens]
        B3[Create Documents]
        B4[Build Vector Index]
        B5[Create Query Engine]
        B6[Query LLM<br/>with FinancialMetrics schema]
        B7[Parse Response]
        B8[Return FinancialMetrics]
        
        B1 --> B2 --> B3 --> B4 --> B5 --> B6 --> B7 --> B8
    end
    
    subgraph RefinedFlow["Refined Extraction Flow"]
        R1[Parse PDF with LlamaParse<br/>to Markdown]
        R2[Filter Sections<br/>Item 7 & 8]
        R3[Create Documents]
        R4[Build Vector Index]
        R5[Create Query Engine<br/>similarity_top_k=10]
        R6[Query LLM<br/>with detailed instructions]
        R7[Parse Response]
        R8[Return FinancialMetrics]
        
        R1 --> R2 --> R3 --> R4 --> R5 --> R6 --> R7 --> R8
    end
    
    BothFlow --> BaselineFlow
    BothFlow --> RefinedFlow
    
    BaselineFlow --> Results[Results Dictionary]
    RefinedFlow --> Results
    
    Results --> EvalCheck{Evaluate?}
    
    EvalCheck -->|Yes| EvalFlow[Evaluation Flow]
    EvalCheck -->|No| SaveResults[Save JSON Results]
    
    subgraph EvalFlow["Evaluation Flow"]
        E1[Load Ground Truth CSV]
        E2[Compare Each Metric]
        E3[Calculate Accuracy]
        E4[Classify Errors]
        E5[Generate Report]
        
        E1 --> E2 --> E3 --> E4 --> E5
    end
    
    EvalFlow --> SaveEval[Save Evaluation JSON]
    SaveResults --> End([End])
    SaveEval --> End
    
    style BaselineFlow fill:#e1f5ff
    style RefinedFlow fill:#fff4e1
    style EvalFlow fill:#ffe1f5
```

---

## State Diagram

```mermaid
stateDiagram-v2
    [*] --> Initialized: System Start
    
    Initialized --> Configuring: Load Environment
    Configuring --> ConfigCheck{API Keys<br/>Available?}
    
    ConfigCheck -->|OpenAI| OpenAIReady: OpenAI Config
    ConfigCheck -->|Ollama| OllamaReady: Ollama Config
    ConfigCheck -->|Both| BothReady: Both Available
    
    OpenAIReady --> ModelInit: Initialize Models
    OllamaReady --> ModelInit: Initialize Models
    BothReady --> ModelInit: Initialize Models
    
    ModelInit --> LLMReady: LLM Initialized
    ModelInit --> EmbedReady: Embeddings Initialized
    
    LLMReady --> ExtractorReady: Extractors Ready
    EmbedReady --> ExtractorReady: Extractors Ready
    
    ExtractorReady --> Processing: Start Processing
    
    state Processing {
        [*] --> FileLoaded: Load Input File
        FileLoaded --> TextExtracted: Extract Text
        TextExtracted --> Chunked: Chunk Text
        Chunked --> Indexed: Build Vector Index
        Indexed --> Querying: Query LLM
        Querying --> Parsed: Parse Response
        Parsed --> [*]: Metrics Extracted
    }
    
    Processing --> Evaluating: Evaluation Mode
    Processing --> Completed: No Evaluation
    
    Evaluating --> Comparing: Compare with Ground Truth
    Comparing --> Calculating: Calculate Accuracy
    Calculating --> Classifying: Classify Errors
    Classifying --> Completed: Evaluation Done
    
    Completed --> [*]: Save Results
    
    note right of ConfigCheck
        Checks for:
        - OPENAI_API_KEY
        - LLAMA_CLOUD_API_KEY
        - USE_OLLAMA flag
        - Ollama server status
    end note
    
    note right of Processing
        Can process:
        - PDF files (both methods)
        - HTML files (baseline only)
    end note
```

---

## Sequence Diagram

```mermaid
sequenceDiagram
    participant User
    participant Main
    participant BE as BaselineExtractor
    participant RE as RefinedExtractor
    participant Parser as PDF/HTML Parser
    participant Index as VectorStoreIndex
    participant LLM as LLM Service
    participant Eval as Evaluator
    participant GT as Ground Truth
    
    User->>Main: Run extraction (--mode both)
    Main->>Main: Load configuration & API keys
    Main->>Main: Filter PDFs by ground truth
    
    loop For each PDF/HTML file
        Main->>BE: Initialize BaselineExtractor
        BE->>BE: Initialize LLM & Embeddings
        BE->>Parser: extract_text_from_pdf/html()
        Parser-->>BE: Raw text
        
        BE->>BE: _chunk_text() (1024 tokens)
        BE->>Index: from_documents()
        Index-->>BE: VectorStoreIndex
        
        BE->>Index: as_query_engine(output_cls=FinancialMetrics)
        Index-->>BE: QueryEngine
        
        BE->>LLM: query(extraction_prompt)
        LLM-->>BE: FinancialMetrics object
        
        BE-->>Main: FinancialMetrics (baseline)
        
        alt Refined mode
            Main->>RE: Initialize RefinedExtractor
            RE->>RE: Initialize LlamaParse parser
            RE->>Parser: load_data() (PDF to Markdown)
            Parser-->>RE: Markdown documents
            
            RE->>RE: _filter_relevant_sections()
            RE->>Index: from_documents()
            Index-->>RE: VectorStoreIndex
            
            RE->>Index: as_query_engine(similarity_top_k=10)
            Index-->>RE: QueryEngine
            
            RE->>LLM: query(detailed_extraction_prompt)
            LLM-->>RE: FinancialMetrics object
            
            RE-->>Main: FinancialMetrics (refined)
        end
        
        alt Evaluation mode
            Main->>Eval: Initialize Evaluator
            Eval->>GT: Load ground_truth.csv
            GT-->>Eval: Ground truth data
            
            Main->>Eval: evaluate(baseline_metrics)
            Eval->>Eval: Compare CIK (exact match)
            Eval->>Eval: Compare Revenue (1% tolerance)
            Eval->>Eval: Compare Net Income (1% tolerance)
            Eval->>Eval: Calculate accuracy
            Eval->>Eval: Classify errors
            Eval-->>Main: Evaluation results
            
            alt Refined mode
                Main->>Eval: evaluate(refined_metrics)
                Eval-->>Main: Evaluation results
            end
        end
        
        Main->>Main: Save results to JSON
    end
    
    Main-->>User: Extraction complete
```

---

## Extraction Pipeline Flow

### Baseline Extraction Pipeline

```mermaid
graph LR
    subgraph "Input"
        A[PDF/HTML File]
    end
    
    subgraph "Text Extraction"
        B[PyPDF/BeautifulSoup]
        C[Raw Text]
    end
    
    subgraph "Text Processing"
        D[Chunk Text<br/>1024 tokens]
        E[Text Chunks]
    end
    
    subgraph "Vectorization"
        F[Create Documents]
        G[Generate Embeddings]
        H[Vector Store Index]
    end
    
    subgraph "Query & Extraction"
        I[Query Engine<br/>similarity_top_k=5]
        J[LLM Query<br/>with FinancialMetrics schema]
        K[Structured Response]
    end
    
    subgraph "Output"
        L[FinancialMetrics Object]
    end
    
    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
    I --> J
    J --> K
    K --> L
    
    style A fill:#ffcccc
    style L fill:#ccffcc
    style J fill:#ccccff
```

### Refined Extraction Pipeline

```mermaid
graph LR
    subgraph "Input"
        A[PDF File]
    end
    
    subgraph "Advanced Parsing"
        B[LlamaParse]
        C[Markdown Documents<br/>preserves tables]
    end
    
    subgraph "Section Filtering"
        D[Filter Item 7 & 8]
        E[Relevant Documents]
    end
    
    subgraph "Vectorization"
        F[Create Documents]
        G[Generate Embeddings]
        H[Vector Store Index]
    end
    
    subgraph "Query & Extraction"
        I[Query Engine<br/>similarity_top_k=10]
        J[LLM Query<br/>table-aware instructions]
        K[Structured Response]
    end
    
    subgraph "Output"
        L[FinancialMetrics Object]
    end
    
    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
    I --> J
    J --> K
    K --> L
    
    style A fill:#ffcccc
    style L fill:#ccffcc
    style J fill:#ccccff
    style C fill:#ffffcc
```

---

## Evaluation Flow

```mermaid
flowchart TD
    Start([Extracted Metrics]) --> LoadGT[Load Ground Truth CSV]
    LoadGT --> ForEach{For Each Metric}
    
    ForEach --> CIK{CIK?}
    ForEach --> Revenue{Total Revenue?}
    ForEach --> Income{Net Income?}
    
    CIK --> CIKCheck[Compare Strings<br/>Normalize & Pad to 10 digits]
    CIKCheck --> CIKMatch{Match?}
    CIKMatch -->|Yes| CIKPass[✓ Match]
    CIKMatch -->|No| CIKFail[✗ Mismatch]
    
    Revenue --> RevCheck[Compare Numeric<br/>Calculate Relative Error]
    RevCheck --> RevTol{Error ≤ 1%?}
    RevTol -->|Yes| RevPass[✓ Match]
    RevTol -->|No| RevFail[✗ Mismatch]
    
    Income --> IncCheck[Compare Numeric<br/>Calculate Relative Error]
    IncCheck --> IncTol{Error ≤ 1%?}
    IncTol -->|Yes| IncPass[✓ Match]
    IncTol -->|No| IncFail[✗ Mismatch]
    
    CIKPass --> Classify
    CIKFail --> Classify
    RevPass --> Classify
    RevFail --> Classify
    IncPass --> Classify
    IncFail --> Classify
    
    Classify[Classify Error Type] --> CalcAcc[Calculate Accuracy<br/>matches / total]
    CalcAcc --> GenReport[Generate Report]
    GenReport --> Save[Save Evaluation JSON]
    Save --> End([End])
    
    style CIKPass fill:#ccffcc
    style RevPass fill:#ccffcc
    style IncPass fill:#ccffcc
    style CIKFail fill:#ffcccc
    style RevFail fill:#ffcccc
    style IncFail fill:#ffcccc
```

---

## Key Components Description

### 1. **FinancialMetrics (Pydantic Model)**
- **Purpose**: Structured data model for extracted financial metrics
- **Fields**:
  - `company_ticker`: Company stock symbol
  - `fiscal_year`: Fiscal year of the report
  - `cik`: Central Index Key (10-digit identifier)
  - `total_revenue`: Total revenue in millions USD
  - `net_income`: Net income in millions USD
- **Validation**: Automatic type conversion and CIK formatting

### 2. **BaselineExtractor**
- **Approach**: Naive text chunking
- **Text Extraction**: PyPDF (PDF) or BeautifulSoup (HTML)
- **Chunking**: 1024-token chunks
- **Vector Search**: similarity_top_k=5
- **Limitation**: Loses table structure

### 3. **RefinedExtractor**
- **Approach**: Table-preserving Markdown parsing
- **Text Extraction**: LlamaParse (PDF to Markdown)
- **Section Filtering**: Focuses on Item 7 & 8
- **Vector Search**: similarity_top_k=10
- **Advantage**: Maintains table row-column relationships

### 4. **Evaluator**
- **Purpose**: Compare extracted metrics with ground truth
- **CIK Comparison**: Exact string match (normalized to 10 digits)
- **Numeric Comparison**: Relative error ≤ 1% tolerance
- **Error Classification**: None, Minor, Moderate, Major
- **Output**: Accuracy percentage and detailed metrics

### 5. **Model Configuration**
- **OpenAI**: GPT-4o for LLM, OpenAI embeddings
- **Ollama**: Local LLM server (gpt-oss:20b), custom embeddings (nomic-embed-text)
- **Fallback**: Automatic fallback if primary service unavailable

---

## Data Structures

### FinancialMetrics Schema
```json
{
  "company_ticker": "AAPL",
  "fiscal_year": 2024,
  "cik": "0000320193",
  "total_revenue": 383285.0,
  "net_income": 96995.0
}
```

### Evaluation Results Schema
```json
{
  "ticker": "AAPL",
  "metrics": {
    "cik": {
      "extracted": "0000320193",
      "ground_truth": "0000320193",
      "match": true,
      "error_type": "None (exact match)"
    },
    "total_revenue": {
      "extracted": 383285.0,
      "ground_truth": 383285.0,
      "match": true,
      "absolute_error": 0.0,
      "relative_error": 0.0,
      "error_type": "None (within tolerance)"
    }
  },
  "accuracy": 1.0
}
```

---

## Configuration Flow

```mermaid
graph TD
    Start([System Start]) --> Env[Load .env file]
    Env --> CheckOllama{USE_OLLAMA<br/>set?}
    
    CheckOllama -->|Yes| OllamaConfig[Ollama Configuration]
    CheckOllama -->|No| OpenAIConfig[OpenAI Configuration]
    
    OllamaConfig --> CheckOllamaServer{Ollama Server<br/>Running?}
    CheckOllamaServer -->|Yes| InitOllamaLLM[Initialize Ollama LLM]
    CheckOllamaServer -->|No| Error1[Error: Server not running]
    
    InitOllamaLLM --> CheckEmbed{Embeddings<br/>Available?}
    CheckEmbed -->|Yes| UseOllamaEmbed[Use Ollama Embeddings]
    CheckEmbed -->|No| CheckOpenAIKey{OpenAI Key<br/>Available?}
    
    CheckOpenAIKey -->|Yes| FallbackEmbed[Fallback to OpenAI Embeddings]
    CheckOpenAIKey -->|No| Error2[Error: No embeddings available]
    
    OpenAIConfig --> CheckOpenAIKey2{OpenAI Key<br/>Available?}
    CheckOpenAIKey2 -->|Yes| InitOpenAILLM[Initialize OpenAI LLM]
    CheckOpenAIKey2 -->|No| Error3[Error: API key required]
    
    InitOpenAILLM --> InitOpenAIEmbed[Initialize OpenAI Embeddings]
    
    UseOllamaEmbed --> Ready[System Ready]
    FallbackEmbed --> Ready
    InitOpenAIEmbed --> Ready
    
    Error1 --> End([Exit])
    Error2 --> End
    Error3 --> End
    Ready --> Process[Start Processing]
    
    style Ready fill:#ccffcc
    style Error1 fill:#ffcccc
    style Error2 fill:#ffcccc
    style Error3 fill:#ffcccc
```

---

## Notes

1. **Dual Extraction Methods**: The system supports both baseline (simple) and refined (advanced) extraction methods for comparison.

2. **Flexible Input**: Supports both PDF and HTML files, though refined extraction (LlamaParse) only works with PDFs.

3. **Model Flexibility**: Can use either OpenAI (cloud) or Ollama (local) for LLM inference, with automatic fallback mechanisms.

4. **Structured Output**: Uses Pydantic models to ensure type safety and validation of extracted data.

5. **Evaluation Framework**: Comprehensive evaluation system that compares extracted values against ground truth with configurable tolerance.

6. **Error Handling**: Multiple fallback mechanisms ensure the system continues operating even if some components fail.

