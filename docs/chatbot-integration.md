# Chatbot Integration

## Overview

The AI & Humanoid Robotics course documentation includes an integrated chatbot that allows readers to ask questions about the content directly from the documentation pages. The chatbot uses a RAG (Retrieval Augmented Generation) system to provide accurate, context-aware responses grounded in the course materials.

## Features

- **Embedded Q&A**: Ask questions about the documentation content without leaving the page
- **Text Selection Context**: Select text on the page and ask specific questions about it
- **Citation Links**: Responses include links to source materials for verification
- **Confidence Scores**: Each response includes a confidence score indicating reliability
- **Conversation History**: Maintain context across multiple queries in a session

## How to Use

### Basic Questions

1. Type your question in the chat input field at the bottom of any documentation page
2. Press Enter or click "Send" to submit your query
3. The AI will process your question and provide a response with supporting citations

### Context-Aware Queries

1. Select text on the current page that you'd like to ask about
2. Type your question in the chat input field
3. The selected text will be provided as context to the AI
4. Submit your query to get a response specifically about the selected content

## Technical Architecture

The chatbot is built using:
- **Frontend**: React components integrated into the Docusaurus documentation site
- **Backend**: FastAPI RAG system with Qdrant vector database
- **AI**: Google Gemini for response generation with OpenAI Agent SDK for orchestration
- **Data**: Course content indexed in Qdrant for semantic search

## API Endpoints

The chatbot communicates with the backend through the following API:

### POST /api/v1/rag/query

Submit a query to the RAG system.

**Request Body:**
```json
{
  "query": "string - The user's question",
  "selectedText": "string - Optional selected text for context",
  "scope": "string - Query scope (course, modules, readings, assignments, general)",
  "conversationId": "string - Optional conversation ID to maintain context"
}
```

**Response:**
```json
{
  "id": "string - Unique response ID",
  "query": "string - Original query",
  "response": "string - AI-generated response",
  "citations": [
    {
      "url": "string - Source URL",
      "module": "string - Module name",
      "chunkId": "number - Chunk position in document",
      "textPreview": "string - Preview of cited text"
    }
  ],
  "confidence": "number - Confidence score (0.0-1.0)",
  "retrievedChunksCount": "number - Number of chunks retrieved",
  "processingTimeMs": "number - Processing time in milliseconds",
  "conversationId": "string - Conversation identifier"
}
```

## Troubleshooting

### Common Issues

1. **"Unable to reach backend service"**: Ensure the backend server is running and accessible
2. **Slow responses**: Large queries or complex questions may take longer to process
3. **Low confidence responses**: Some questions may not have clear answers in the documentation

### Error Codes

- `INVALID_QUERY`: Query text is required and cannot be empty
- `RATE_LIMIT_EXCEEDED`: Too many requests, please wait before trying again
- `CONTENT_FILTERED`: Query was filtered due to safety policies
- `SERVICE_UNAVAILABLE`: Backend service is temporarily unavailable

## Development

For developers looking to extend or modify the chatbot functionality:

1. The React components are located in `src/components/Chatbot/`
2. The API client is in `static/js/api-client.js`
3. Backend implementation is in the `backend/` directory
4. Styling is in `src/components/Chatbot/Chatbot.module.css`

## Privacy & Security

- All queries are processed securely on the backend
- No personal information is stored or transmitted
- Conversations are temporary and not persisted beyond the session