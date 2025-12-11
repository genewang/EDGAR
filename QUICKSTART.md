# Quick Start Guide: 10-K Extraction System

This guide will help you get started with extracting financial metrics from 10-K PDFs.

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Set Up API Keys

### Option A: Using OpenAI (Default)

Create a `.env` file:

```bash
OPENAI_API_KEY=your_openai_key_here
LLAMA_CLOUD_API_KEY=your_llama_cloud_key_here
```

**Get API Keys:**
- OpenAI: https://platform.openai.com/api-keys
- LlamaCloud: https://cloud.llamaindex.ai/ (free tier available)

### Option B: Using Local Ollama Server

To use a local Ollama server instead of OpenAI:

1. **Install Ollama** (if not already installed):
   ```bash
   # Visit https://ollama.com/ for installation instructions
   ```

2. **Pull the model**:
   ```bash
   ollama pull gpt-oss:20b
   ```

3. **Start Ollama server** (if not running):
   ```bash
   ollama serve
   ```

4. **Install Ollama support**:
   ```bash
   pip install llama-index-llms-ollama
   ```

5. **Run with Ollama flag**:
   ```bash
   python extract_10k_data.py --mode both --use-ollama --pdf-dir pdfs
   ```

   Or set environment variable:
   ```bash
   USE_OLLAMA=true python extract_10k_data.py --mode both --pdf-dir pdfs
   ```

**Configuration Options:**
- `--use-ollama`: Use local Ollama server instead of OpenAI
- `--ollama-model MODEL`: Specify Ollama model (default: `gpt-oss:20b`)
- `--ollama-base-url URL`: Specify Ollama server URL (default: `http://localhost:11434`)
- Environment variables: `USE_OLLAMA`, `OLLAMA_MODEL`, `OLLAMA_BASE_URL`

## Step 3: Populate Ground Truth (Optional but Recommended)

You can either:
- Manually edit `ground_truth.csv` with values from the PDFs
- Or run the interactive helper: `python populate_ground_truth.py`

## Step 4: Run Extraction

### Test with Baseline Only (No LlamaCloud Key Needed)

```bash
python extract_10k_data.py --mode baseline --pdf-dir pdfs
```

### Run Both Methods (Recommended)

**With OpenAI:**
```bash
python extract_10k_data.py --mode both --pdf-dir pdfs --evaluate
```

**With Ollama:**
```bash
python extract_10k_data.py --mode both --pdf-dir pdfs --evaluate --use-ollama
```

This will:
1. Extract metrics using both baseline and refined methods
2. Compare against ground truth (if available)
3. Generate evaluation report

## Step 5: Review Results

Check the output files:
- `extraction_results.json`: Raw extraction results
- `evaluation_extraction_results.json`: Evaluation metrics (if `--evaluate` used)

## Expected Output

```
Processing AAPL: AAPL_Apple_10K_0000.pdf
  Running baseline extraction...
  [Baseline] Extracting text from PDF...
  [Baseline] Creating vector index...
  [Baseline] Querying LLM for financial metrics...
  ✓ Baseline extraction complete
  Running refined extraction...
  [Refined] Parsing PDF with LlamaParse...
  [Refined] Creating vector index from 45 documents...
  [Refined] Querying LLM for financial metrics...
  ✓ Refined extraction complete
```

## Troubleshooting

### "OPENAI_API_KEY not found"
- Make sure `.env` file exists in the project root
- Check that the key is correct (starts with `sk-`)

### "LlamaParse not available"
- Install: `pip install llama-parse`
- Get free API key from https://cloud.llamaindex.ai/
- Add to `.env` as `LLAMA_CLOUD_API_KEY`

### "Ollama support requested but llama-index-llms-ollama is not installed"
- Install: `pip install llama-index-llms-ollama`
- Make sure Ollama server is running: `ollama serve`
- Verify model is available: `ollama list`

### Low Accuracy
- Verify ground truth values are correct
- Check that PDFs are readable
- Try refined method (better for tables)

## Next Steps

1. Review extraction results
2. Analyze errors in evaluation report
3. Refine prompts or add post-processing
4. Iterate on improvements

