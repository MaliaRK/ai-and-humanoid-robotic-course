# API Contract: Vector Retrieval Service

## Endpoints

### POST /retrieve
Perform semantic search against the vector database and return relevant content chunks.

#### Request
```json
{
  "query": "semantic search query string",
  "top_k": 5,
  "similarity_threshold": 0.5,
  "filters": {
    "module_name": "optional module filter",
    "source_url": "optional source filter"
  }
}
```

#### Response (Success 200)
```json
{
  "query": "semantic search query string",
  "results": [
    {
      "text": "retrieved content chunk text",
      "similarity_score": 0.85,
      "metadata": {
        "source_url": "https://source-url.com",
        "module_name": "module name",
        "chunk_index": 0
      }
    }
  ],
  "retrieval_time_ms": 120.5,
  "total_candidates": 150
}
```

#### Response (Error 400)
```json
{
  "error": "Invalid request parameters",
  "details": "top_k must be between 1 and 100"
}
```

#### Response (Error 500)
```json
{
  "error": "Internal server error",
  "details": "Error connecting to vector database"
}
```

### GET /health
Check the health status of the retrieval service.

#### Response (Success 200)
```json
{
  "status": "healthy",
  "timestamp": "2025-12-14T10:30:00Z",
  "dependencies": {
    "qdrant": "connected",
    "cohere": "reachable"
  }
}
```

### POST /validate
Validate the retrieval pipeline with a test query and return validation metrics.

#### Request
```json
{
  "test_query": "validation query string",
  "expected_sources": ["expected source URLs"],
  "metrics": ["relevance_score", "latency", "metadata_accuracy"]
}
```

#### Response (Success 200)
```json
{
  "query": "validation query string",
  "results": [
    {
      "text": "retrieved content chunk text",
      "similarity_score": 0.85,
      "metadata": {
        "source_url": "https://source-url.com",
        "module_name": "module name",
        "chunk_index": 0
      }
    }
  ],
  "validation_metrics": {
    "relevance_score": 0.92,
    "latency_ms": 120.5,
    "metadata_accuracy": 1.0,
    "expected_sources_found": 3,
    "unexpected_sources_found": 0
  },
  "passed": true
}
```

## Data Types

### QueryRequest
- query: string (required) - The search query text
- top_k: integer (optional, default: 5) - Number of results to return (1-100)
- similarity_threshold: number (optional, default: 0.5) - Minimum similarity threshold (0.0-1.0)
- filters: Filters (optional) - Additional filters to apply

### Filters
- module_name: string (optional) - Filter by specific module name
- source_url: string (optional) - Filter by specific source URL

### RetrievalResult
- text: string (required) - The retrieved content chunk
- similarity_score: number (required) - Cosine similarity score (0.0-1.0)
- metadata: MetadataPackage (required) - Associated metadata

### MetadataPackage
- source_url: string (required) - Original source URL
- module_name: string (required) - Module/chapter name
- chunk_index: integer (required) - Position of chunk in original document

### ValidationResult
- relevance_score: number (required) - Overall relevance score (0.0-1.0)
- latency_ms: number (required) - Retrieval time in milliseconds
- metadata_accuracy: number (required) - Accuracy of metadata preservation (0.0-1.0)
- expected_sources_found: integer (required) - Count of expected sources found
- unexpected_sources_found: integer (required) - Count of unexpected sources found
- passed: boolean (required) - Whether validation passed overall criteria