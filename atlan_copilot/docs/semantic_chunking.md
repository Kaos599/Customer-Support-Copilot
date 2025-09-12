# Semantic Chunker Implementation

This document describes the semantic chunking implementation using LangGraph for the Atlan Customer Support Copilot.

## Overview

The semantic chunker replaces the traditional character-based chunking with an intelligent, meaning-aware approach that creates chunks based on semantic similarity rather than fixed character counts.

## Key Features

### 🧠 Semantic Awareness
- Uses embeddings to understand text meaning
- Creates chunks at natural semantic boundaries
- Preserves context and relationships between concepts

### 🔄 LangGraph Workflow
- **Sentence Splitting**: Breaks text into sentences
- **Embedding Generation**: Creates vector representations for each sentence
- **Boundary Detection**: Finds optimal split points based on similarity
- **Chunk Refinement**: Ensures chunks meet size requirements

### 📊 Intelligent Chunking
- **Similarity Threshold**: Configurable threshold (0-1) for semantic boundaries
- **Size Constraints**: Minimum and maximum chunk sizes
- **Fallback Mechanism**: Character-based chunking if semantic fails

## Configuration Parameters

```python
chunker = SemanticChunker(
    similarity_threshold=0.7,  # Lower = more chunks, Higher = fewer chunks
    min_chunk_size=500,        # Minimum characters per chunk
    max_chunk_size=2000        # Maximum characters per chunk
)
```

## How It Works

### 1. Text Preprocessing
- Clean whitespace and formatting
- Split into sentences using regex patterns

### 2. Embedding Generation
- Generate embeddings for each sentence using Gemini
- Process in batches to avoid rate limits

### 3. Semantic Boundary Detection
- Calculate cosine similarity between consecutive sentences
- Split chunks when similarity falls below threshold
- Merge small chunks to meet minimum size requirements

### 4. Chunk Refinement
- Ensure all chunks meet size constraints
- Use recursive character splitting for oversized chunks
- Maintain semantic coherence

## Benefits Over Character-Based Chunking

### 🎯 Better Context Preservation
- Chunks end at natural topic boundaries
- Related concepts stay together
- Improved retrieval relevance

### 📈 Enhanced Retrieval Performance
- More meaningful chunks for embedding
- Better semantic matching
- Reduced noise in search results

### 🔧 Adaptive Chunking
- Adjusts to content structure
- Handles varying text complexity
- Maintains readability

## Usage Examples

### Basic Usage
```python
from scrapers.semantic_chunker import SemanticChunker

chunker = SemanticChunker()
chunks = await chunker.chunk_text("Your text here...")
```

### With Custom Parameters
```python
chunker = SemanticChunker(
    similarity_threshold=0.8,  # More conservative splitting
    min_chunk_size=300,
    max_chunk_size=1500
)
```

### Document Processing
```python
documents = [
    {
        "url": "https://example.com/doc",
        "title": "Document Title",
        "content": "Full document text...",
        "source": "example.com"
    }
]

processed_chunks = chunker.process_documents(documents)
```

## Integration with Vector Store

The semantic chunks integrate seamlessly with the existing vector store pipeline:

1. **Content Processing**: `ContentProcessor` uses `SemanticChunker`
2. **Embedding Generation**: Each chunk gets embedded using Gemini
3. **Vector Storage**: Chunks stored in Qdrant with metadata
4. **Retrieval**: Semantic chunks improve search relevance

## Performance Considerations

### ⚡ Efficiency
- Batch processing for embeddings
- Asynchronous operations
- Memory-efficient streaming

### 🔒 Reliability
- Fallback to character-based chunking
- Error handling and recovery
- Rate limit management

### 📏 Scalability
- Configurable batch sizes
- Memory usage optimization
- Parallel processing support

## Testing

Run the test script to see the semantic chunker in action:

```bash
cd atlan_copilot
python -m scripts.test_semantic_chunker
```

## Future Enhancements

### 🤖 Advanced NLP
- Named entity recognition
- Topic modeling integration
- Multi-language support

### 🎛️ Dynamic Parameters
- Content-adaptive thresholds
- Learning-based optimization
- User feedback integration

### 🔗 Enhanced Integration
- Support for different embedding models
- Custom similarity metrics
- Hierarchical chunking

## Dependencies

- `langgraph`: Workflow orchestration
- `scikit-learn`: Similarity calculations
- `langchain`: Text splitting utilities
- `google-generativeai`: Embedding generation

## Configuration

Update your `.env` file with necessary API keys:

```env
GEMINI_API_KEY=your_api_key_here
GOOGLE_API_KEY=your_api_key_here
```

The semantic chunker is now the default chunking method in the content processing pipeline, providing more intelligent and context-aware text segmentation for improved RAG performance.
