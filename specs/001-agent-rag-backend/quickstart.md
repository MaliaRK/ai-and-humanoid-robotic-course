# Quickstart Guide: Agentic RAG Backend

## Prerequisites

- Python 3.10 or higher
- Access to OpenAI API (for Agent SDK)
- Access to Google Gemini API
- Qdrant vector database access
- Neon Postgres database access

## Setup

### 1. Clone and Navigate to Project
```bash
git clone <repository-url>
cd <project-root>
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file based on the `.env.example` template:

```bash
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_api_key
NEON_DATABASE_URL=your_neon_database_url
```

## Running the Service

### 1. Start the FastAPI Service
```bash
cd backend
uvicorn api.main:app --reload --port 8000
```

### 2. Verify Service is Running
The API will be available at `http://localhost:8000`

Check the health endpoint:
```bash
curl http://localhost:8000/api/v1/rag/health
```

## Making Your First Query

### 1. Send a Query to the RAG System
```bash
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the principles of humanoid robotics?",
    "scope": null
  }'
```

### 2. Expected Response
You should receive a response with:
- Generated answer grounded in retrieved content
- Citations with source metadata (URL, module, chunk_id)
- Confidence score
- Processing time

## Development

### Running Tests
```bash
cd backend
pytest tests/
```

### API Documentation
FastAPI automatically generates API documentation:
- Interactive docs: `http://localhost:8000/docs`
- Alternative Swagger UI: `http://localhost:8000/redoc`

## Configuration

### Agent Settings
The agent behavior can be configured through environment variables:
- `AGENT_MODEL`: OpenAI model to use for agent orchestration
- `AGENT_TEMPERATURE`: Temperature setting for response creativity
- `MAX_RETRIEVAL_CHUNKS`: Maximum number of chunks to retrieve (default: 5)

### Retrieval Settings
- `QDRANT_COLLECTION_NAME`: Name of the Qdrant collection to search
- `RETRIEVAL_TOP_K`: Number of top results to retrieve (default: 5)
- `SIMILARITY_THRESHOLD`: Minimum similarity score for inclusion (default: 0.3)

### Database Settings
- `DATABASE_POOL_SIZE`: Connection pool size for Neon Postgres
- `DATABASE_POOL_TIMEOUT`: Connection timeout in seconds