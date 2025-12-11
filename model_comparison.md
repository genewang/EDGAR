# Ollama Model Comparison for Financial Document Extraction

## Available Models

### Current Model: `gpt-oss:20b`
- **Size**: 13 GB
- **Parameters**: 20B
- **Pros**: Large model, good reasoning
- **Cons**: Very large, memory intensive, slower inference
- **Best for**: Complex reasoning tasks

### Recommended Alternatives

#### 1. **llama3.1:8b** ⭐ RECOMMENDED
- **Size**: ~4.9 GB
- **Parameters**: 8B
- **Pros**: 
  - Excellent instruction following
  - Strong JSON/structured output generation
  - Good balance of performance and efficiency
  - Faster inference than 20B models
  - Better memory efficiency
- **Cons**: Slightly less capable than larger models
- **Best for**: Structured extraction, JSON generation, table understanding

#### 2. **qwen2.5:14b** ⭐ GOOD ALTERNATIVE
- **Size**: ~9.0 GB
- **Parameters**: 14B
- **Pros**:
  - Strong performance on structured tasks
  - Good multilingual support
  - Better than 8B models for complex reasoning
- **Cons**: Larger than 8B, slower inference
- **Best for**: Complex financial analysis, multilingual documents

#### 3. **mistral:7b**
- **Size**: ~4.4 GB
- **Parameters**: 7B
- **Pros**: Smallest, fastest inference
- **Cons**: Less capable than larger models
- **Best for**: Quick prototyping, resource-constrained environments

## Recommendation for Your Use Case

For **financial document extraction with Pydantic structured output**, I recommend:

1. **Primary**: `llama3.1:8b` - Best balance of performance and efficiency
2. **Alternative**: `qwen2.5:14b` - If you need more reasoning capability
3. **Current**: `gpt-oss:20b` - Only if you have memory to spare and need maximum capability

## Performance Comparison

| Model | Size | Speed | JSON Quality | Table Understanding | Memory Usage |
|-------|------|-------|--------------|---------------------|-------------|
| llama3.1:8b | 4.9GB | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Low |
| qwen2.5:14b | 9.0GB | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Medium |
| gpt-oss:20b | 13GB | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | High |
| mistral:7b | 4.4GB | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Very Low |

## Next Steps

Test `llama3.1:8b` with your extraction pipeline to see improved performance and faster processing times.

