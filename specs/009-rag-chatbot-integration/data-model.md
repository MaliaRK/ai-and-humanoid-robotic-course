# Data Model: Frontend and Backend Integration for RAG Chatbot

## Overview
This document defines the data structures and entities for the chatbot integration between Docusaurus frontend and FastAPI RAG backend.

## Entities

### Query
A question submitted by the user, including optional selected text context and metadata.

**Fields**:
- `id`: string (auto-generated UUID)
- `query`: string (required, user's question text)
- `selectedText`: string (optional, text selected on the current page)
- `context`: string (optional, additional context from page)
- `timestamp`: datetime (when the query was created)
- `conversationId`: string (optional, for maintaining conversation context)

**Validation Rules**:
- Query text must be between 3-1000 characters
- Selected text must be between 10-5000 characters if provided
- Query text cannot be empty or whitespace only

### Response
The AI-generated answer from the backend, including citations and confidence information.

**Fields**:
- `id`: string (auto-generated UUID)
- `queryId`: string (reference to the original query)
- `response`: string (the AI-generated answer)
- `citations`: array of Citation objects (references to source material)
- `confidence`: number (0.0-1.0 confidence score)
- `retrievedChunksCount`: number (how many chunks were retrieved)
- `processingTimeMs`: number (time taken to process in milliseconds)
- `timestamp`: datetime (when the response was generated)

**Validation Rules**:
- Response text must be between 10-10000 characters
- Confidence score must be between 0.0 and 1.0
- Citations array can be empty but must be an array

### Citation
A reference to source material with URL, module, and chunk_id for navigation.

**Fields**:
- `url`: string (URL to the source document)
- `module`: string (module name where the citation is from)
- `chunkId`: number (position of the chunk in the document)
- `textPreview`: string (optional, preview of the cited text)

**Validation Rules**:
- URL must be a valid URL format
- Module name must not be empty
- Chunk ID must be a positive integer
- Text preview can be null or between 10-200 characters

### Conversation
A temporary session context that maintains query-response history during a single browsing session.

**Fields**:
- `id`: string (auto-generated UUID)
- `queries`: array of Query objects (all queries in the conversation)
- `responses`: array of Response objects (all responses in the conversation)
- `createdAt`: datetime (when the conversation started)
- `updatedAt`: datetime (when the conversation was last updated)

**Validation Rules**:
- Conversation ID must be unique per session
- Queries and responses must be in chronological order
- Conversation should expire after 30 minutes of inactivity

## State Transitions

### Query State
- `created` → `sent` → `processing` → `completed`/`failed`

### Conversation State
- `active` → `expired` (after 30 minutes of inactivity)

## Relationships
- A Conversation contains multiple Query-Response pairs
- A Response references a single Query
- A Response contains multiple Citations