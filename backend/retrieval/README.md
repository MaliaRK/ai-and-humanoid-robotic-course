# Vector Retrieval and RAG Pipeline Validation System

This module implements semantic search functionality to retrieve contextually relevant content chunks from the Qdrant vector database based on user queries.

## Overview

The vector retrieval system provides:
- Semantic search capabilities using Gemini embeddings
- Integration with Qdrant vector database
- Metadata preservation and validation
- Performance measurement and optimization
- Comprehensive error handling and logging

## Features

- **Semantic Search**: Query the vector database using natural language queries
- **Configurable Parameters**: Adjustable top-k results and similarity thresholds
- **Metadata Validation**: Ensures metadata integrity during retrieval
- **Performance Monitoring**: Measures and reports retrieval latency
- **Error Handling**: Comprehensive error handling with retry logic
- **Logging**: Detailed logging for debugging and monitoring

## Requirements

- Python 3.10+
- Google Gemini API key
- Qdrant Cloud account and API key
- Required Python packages (see requirements.txt)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```
GEMINI_API_KEY=your_gemini_api_key
QDRANT_URL=your_qdrant_cloud_url
QDRANT_API_KEY=your_qdrant_api_key
WEBSITE_URL=https://ai-and-humanoid-robotic-course.vercel.app/
```

## Usage

### Command Line Interface

Run the retrieval pipeline with default settings:
```bash
python retrieval.py
```

With custom parameters:
```bash
python retrieval.py --query "What is artificial intelligence?" --top-k 10 --threshold 0.5
```

Available options:
- `--query`: Query string to retrieve relevant content for (default: "What does the book say about humanoid robotics?")
- `--top-k`: Number of top results to retrieve (default: 5)
- `--threshold`: Similarity threshold for filtering results (default: 0.3)
- `--collection`: Qdrant collection name (default: "rag_embedding")
- `--verbose`: Enable verbose output for debugging

### Programmatic Usage

```python
from retrieval import initialize_gemini_client, initialize_qdrant_client, retrieve_chunks_for_query_with_retry

# Initialize clients
gemini_client = initialize_gemini_client()
qdrant_client = initialize_qdrant_client()

# Perform retrieval
results = retrieve_chunks_for_query_with_retry(
    gemini_client=gemini_client,
    qdrant_client=qdrant_client,
    query="What is artificial intelligence?",
    top_k=5,
    similarity_threshold=0.3
)

for result in results:
    print(f"Text: {result['text'][:100]}...")
    print(f"Similarity: {result['similarity_score']:.3f}")
    print(f"Source: {result['source_url']}")
    print("---")
```

## API Functions

### `retrieve_chunks_for_query_with_retry(gemini_client, qdrant_client, query, top_k=5, similarity_threshold=0.3, collection_name="rag_embedding", max_retries=3)`

Retrieve semantically similar content chunks for a given query with retry logic.

**Parameters:**
- `gemini_client`: Initialized Gemini client
- `qdrant_client`: Initialized Qdrant client
- `query`: The search query string
- `top_k`: Number of top results to retrieve (default: 5)
- `similarity_threshold`: Minimum similarity score for inclusion (default: 0.3)
- `collection_name`: Qdrant collection name (default: "rag_embedding")
- `max_retries`: Maximum number of retry attempts (default: 3)

**Returns:**
- List of dictionaries containing text, source_url, module_name, chunk_index, and similarity_score

### `validate_metadata_integrity(retrieved_chunks)`

Validate that metadata is preserved and accurate in retrieved chunks.

**Parameters:**
- `retrieved_chunks`: List of retrieved chunks with metadata

**Returns:**
- Tuple of (is_valid, list_of_issues)

## Configuration

The system uses several configuration constants that can be modified in the source code:

- `CHUNK_SIZE`: Size of text chunks in characters (default: 512)
- `CHUNK_OVERLAP`: Overlap between chunks to maintain context (default: 50)
- `MAX_DEPTH`: Maximum depth to crawl for URL discovery (default: 2)
- `REQUEST_TIMEOUT`: Timeout for HTTP requests in seconds (default: 10)
- `MAX_RETRIES`: Maximum number of retries for failed requests (default: 3)
- `EMBEDDING_BATCH_SIZE`: Number of chunks to embed at once (default: 5, reduced for Gemini rate limits)

## Testing

The system includes comprehensive testing functions:

- `test_semantic_search_with_sample_queries()`: Tests semantic search functionality
- `test_metadata_preservation_with_query_types()`: Tests metadata preservation
- `test_retrieval_performance_with_different_configs()`: Tests performance with different configurations
- `test_complete_pipeline_from_query_to_validated_results()`: Tests the complete pipeline

## Logging

The system logs to both console and file (`logs/retrieval_pipeline.log`). Log levels can be adjusted in the `add_logging_configuration()` function.

## Error Handling

The system implements comprehensive error handling with:
- Connection error retries with exponential backoff
- Rate limit handling
- Graceful degradation when API limits are reached
- Detailed error reporting

## Performance

The system is optimized for interactive use with:
- Sub-500ms retrieval latency target
- Configurable result set size (top-k)
- Similarity threshold filtering
- Batch processing for efficiency