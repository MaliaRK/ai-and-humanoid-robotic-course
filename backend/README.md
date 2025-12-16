# Agentic RAG Backend API

A sophisticated backend service that implements an agentic RAG (Retrieval-Augmented Generation) system using OpenAI Agent SDK, Qdrant vector database, and Google Gemini for response generation.

## Overview

The Agentic RAG Backend API provides a complete solution for question-answering over course content with the following key features:

- **Agentic Orchestration**: Uses OpenAI Agent SDK to orchestrate the RAG pipeline
- **Vector Search**: Leverages Qdrant for semantic search and retrieval
- **Response Generation**: Utilizes Google Gemini for high-quality response generation
- **Citation Tracking**: Provides accurate source citations with URL, module, and chunk_id
- **Conversation State**: Maintains conversation context with database persistence
- **API Layer**: FastAPI-based REST API with comprehensive error handling

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Layer     │    │   Agent Layer    │    │   Data Layer    │
│   (FastAPI)     │◄──►│  (OpenAI Agent)  │◄──►│  (Qdrant, DB)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Features

- **Semantic Search**: Advanced vector search capabilities using Qdrant
- **Citation-Aware Responses**: All responses include proper source citations
- **Conversation Tracking**: Maintains conversation state across queries
- **Query Scoping**: Supports different query scopes (course, modules, readings, etc.)
- **Rate Limiting**: Built-in rate limiting to prevent abuse
- **Comprehensive Logging**: Detailed logging for monitoring and debugging
- **Error Handling**: Robust error handling with graceful degradation
- **Performance Monitoring**: Built-in performance metrics and timing

## API Endpoints

### Main Endpoints

- `POST /api/v1/rag/query` - Submit a query to the RAG system
- `GET /api/v1/rag/health` - Health check for RAG services
- `GET /api/v1/rag/conversations/{conversation_id}` - Retrieve conversation history
- `GET /health` - Overall service health check
- `GET /` - Root endpoint

### Query Endpoint

The main query endpoint accepts the following parameters:

```json
{
  "query": "string (required) - The question to answer",
  "scope": "string (optional) - Query scope (course, modules, readings, assignments, general)",
  "conversation_id": "string (optional) - Existing conversation ID to continue"
}
```

**Response Format:**
```json
{
  "id": "string - Unique response ID",
  "query": "string - Original query",
  "response": "string - Generated response",
  "citations": [
    {
      "url": "string - Source URL",
      "module": "string - Module name",
      "chunk_id": "number - Chunk position in document",
      "text_preview": "string - Preview of cited text"
    }
  ],
  "confidence": "number - Confidence score (0.0-1.0)",
  "retrieved_chunks_count": "number - Number of chunks retrieved",
  "processing_time_ms": "number - Processing time in milliseconds",
  "conversation_id": "string - Conversation identifier"
}
```

## Installation

### Prerequisites

- Python 3.10+
- Qdrant vector database
- PostgreSQL (or compatible) database
- API keys for OpenAI and Google Gemini

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd ai-and-humanoid-robotics-course/backend
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file with the following variables:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   GEMINI_API_KEY=your_gemini_api_key
   QDRANT_URL=your_qdrant_url
   QDRANT_API_KEY=your_qdrant_api_key
   NEON_DATABASE_URL=your_postgres_connection_string
   ```

4. **Run the application:**
   ```bash
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for embeddings | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `QDRANT_URL` | Qdrant vector database URL | Yes |
| `QDRANT_API_KEY` | Qdrant API key | No (if using local) |
| `NEON_DATABASE_URL` | PostgreSQL database URL | Yes |
| `QDRANT_COLLECTION_NAME` | Qdrant collection name | No (default: "course_content") |
| `AGENT_MODEL` | OpenAI model for agent (default: "gpt-4") | No |
| `RETRIEVAL_TOP_K` | Number of results to retrieve (default: 5) | No |
| `SIMILARITY_THRESHOLD` | Minimum similarity score (default: 0.3) | No |

## Usage Examples

### Basic Query
```bash
curl -X POST "http://localhost:8000/api/v1/rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the AI & Humanoid Robotics course about?",
    "scope": "course"
  }'
```

### Scoped Query
```bash
curl -X POST "http://localhost:8000/api/v1/rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What topics are covered in module 1?",
    "scope": "modules"
  }'
```

### Conversation Continuation
```bash
curl -X POST "http://localhost:8000/api/v1/rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Can you elaborate on that?",
    "conversation_id": "existing_conversation_id"
  }'
```

## Rate Limiting

The API implements rate limiting to prevent abuse:
- Query endpoint: 10 requests per minute per IP
- Health check: 30 requests per minute per IP
- Conversation retrieval: 20 requests per minute per IP

## Database Schema

The system uses PostgreSQL with the following main tables:

- `conversations` - Stores conversation metadata
- `query_logs` - Logs each query and response
- `citation_logs` - Tracks citations for each query

## Testing

Run the test suite:
```bash
# Unit tests
pytest tests/test_unit.py

# Integration tests
pytest tests/test_integration.py

# API integration tests
pytest tests/test_api_integration.py

# All tests
pytest
```

## Performance

The system is designed to meet the following performance goals:
- Response time: < 5 seconds for typical queries
- Supports concurrent requests
- Efficient database queries with connection pooling
- Caching where appropriate

## Error Handling

The API provides comprehensive error handling:
- Validation errors with detailed messages
- Graceful degradation when services are unavailable
- Proper HTTP status codes
- Structured error responses

## Security

- Input validation on all endpoints
- Rate limiting to prevent abuse
- Secure API key handling
- CORS configuration (currently allows all origins for development)

## Monitoring

The system includes:
- Comprehensive logging with structured format
- Performance timing measurements
- Health check endpoints
- Error tracking

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

[Specify your license here]

## Support

For support, please contact [contact information].