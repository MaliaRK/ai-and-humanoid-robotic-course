# API Contracts: Agentic RAG Backend

## Endpoint: POST /api/v1/rag/query
**Purpose**: Submit a query to the agentic RAG system and receive a grounded response with citations

**Request**:
```json
{
  "query": "What are the principles of humanoid robotics?",
  "scope": "chapter_3" (optional)
}
```

**Request Validation**:
- `query` is required and must be 1-1000 characters
- `scope` is optional and represents a specific section to search within

**Response (Success)**:
```json
{
  "id": "uuid-string",
  "query": "What are the principles of humanoid robotics?",
  "response": "The principles of humanoid robotics include: 1) Biomechanical design that mimics human movement patterns...",
  "citations": [
    {
      "url": "https://ai-and-humanoid-robotic-course.vercel.app/chapter3/principles",
      "module": "chapter_3",
      "chunk_id": 12,
      "text_preview": "The fundamental principles of humanoid robotics are based on..."
    }
  ],
  "confidence": 0.87,
  "retrieved_chunks_count": 3,
  "processing_time_ms": 1250,
  "conversation_id": "uuid-string"
}
```

**Response Validation**:
- `id` is a UUID for the response
- `response` contains the generated answer text
- `citations` is an array of source references with metadata
- `confidence` is a float between 0-1 indicating response quality
- `retrieved_chunks_count` indicates how many chunks were retrieved
- `processing_time_ms` shows the total processing time
- `conversation_id` identifies the conversation session

**Response (Error)**:
```json
{
  "error": "string",
  "message": "detailed error message",
  "code": "error_code"
}
```

**Error Codes**:
- `QUERY_TOO_LONG`: Query exceeds maximum length
- `NO_RELEVANT_CONTENT`: No relevant content found in retrieval
- `AGENT_ERROR`: Agent orchestration failed
- `SERVICE_UNAVAILABLE`: Downstream service unavailable

---

## Endpoint: GET /api/v1/rag/conversations/{conversation_id}
**Purpose**: Retrieve conversation history for debugging and analytics

**Request Parameters**:
- `conversation_id`: UUID of the conversation to retrieve

**Response (Success)**:
```json
{
  "conversation_id": "uuid-string",
  "created_at": "2023-12-15T10:30:00Z",
  "updated_at": "2023-12-15T10:35:00Z",
  "queries": [
    {
      "id": "uuid-string",
      "text": "What are the principles of humanoid robotics?",
      "timestamp": "2023-12-15T10:30:00Z",
      "response": {
        "id": "uuid-string",
        "content": "The principles of humanoid robotics include...",
        "citations": [...],
        "timestamp": "2023-12-15T10:30:05Z"
      }
    }
  ]
}
```

**Response (Error)**:
```json
{
  "error": "CONVERSATION_NOT_FOUND",
  "message": "Conversation with specified ID does not exist",
  "code": "CONVERSATION_NOT_FOUND"
}
```

---

## Endpoint: GET /api/v1/rag/health
**Purpose**: Check the health status of the RAG system and its dependencies

**Response (Success)**:
```json
{
  "status": "healthy",
  "timestamp": "2023-12-15T10:30:00Z",
  "services": {
    "agent": "healthy",
    "qdrant": "healthy",
    "gemini": "healthy",
    "database": "healthy"
  }
}
```

**Response (Error)**:
```json
{
  "status": "unhealthy",
  "timestamp": "2023-12-15T10:30:00Z",
  "services": {
    "agent": "healthy",
    "qdrant": "unhealthy",
    "gemini": "healthy",
    "database": "healthy"
  },
  "error": "Qdrant connection failed"
}
```