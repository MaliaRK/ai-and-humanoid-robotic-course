# Quickstart Guide: Vector Retrieval and RAG Pipeline Validation

## Prerequisites
- Python 3.10+
- Access to Cohere API (with sufficient credits for embedding generation)
- Access to Qdrant Cloud (with vectors already ingested from previous step)
- API keys for both services

## Setup

1. **Clone the repository and navigate to the backend directory**:
   ```bash
   git clone [repository-url]
   cd ai-and-humanoid-robotics-course/backend
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```

   Edit the `.env` file with your actual credentials:
   ```env
   COHERE_API_KEY=your_cohere_api_key
   QDRANT_URL=your_qdrant_cloud_url
   QDRANT_API_KEY=your_qdrant_api_key
   ```

## Basic Usage

1. **Run the retrieval validation script**:
   ```bash
   python -m retrieval.retrieval --query "your search query here"
   ```

2. **Validate retrieval with specific parameters**:
   ```bash
   python -m retrieval.retrieval --query "semantic search query" --top-k 5 --threshold 0.7
   ```

3. **Run validation tests**:
   ```bash
   python -m retrieval.test_queries
   ```

## Configuration

The system supports the following configuration options:

- `--top-k`: Number of results to return (default: 5)
- `--threshold`: Minimum similarity threshold (default: 0.5)
- `--query`: Search query text
- `--module-filter`: Filter results by specific module (optional)

## Output Format

The retrieval system returns results in the following format:
```json
{
  "query": "search query",
  "results": [
    {
      "text": "retrieved content chunk",
      "similarity_score": 0.85,
      "metadata": {
        "source_url": "https://...",
        "module_name": "module name",
        "chunk_index": 0
      }
    }
  ],
  "retrieval_time_ms": 120.5
}
```

## Validation Testing

Run the validation suite to ensure the pipeline is working correctly:
```bash
pytest tests/test_retrieval.py -v
```

This will test:
- Semantic search accuracy
- Metadata preservation
- Performance benchmarks
- Configuration flexibility