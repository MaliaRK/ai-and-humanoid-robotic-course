# Data Model: Agentic RAG Backend

## Entity: Query
**Description**: A user's question or request for information from the book content

**Fields**:
- `id`: UUID (Primary Key) - Unique identifier for the query
- `text`: String (Text) - The actual query text from the user
- `scope`: String (Optional) - Optional scope parameter for scoped queries
- `timestamp`: DateTime - When the query was received
- `conversation_id`: UUID (Foreign Key) - Links to the conversation

**Validation Rules**:
- Text must not be empty
- Text must be between 1-1000 characters
- Scope is optional but if provided, must be valid

## Entity: RetrievedChunk
**Description**: A segment of book content retrieved from Qdrant with associated metadata

**Fields**:
- `id`: UUID (Primary Key) - Unique identifier for the chunk
- `content`: String (Text) - The actual text content of the chunk
- `source_url`: String (URL) - URL where the content was found
- `module_name`: String (Text) - Name of the module/chapter
- `chunk_id`: Integer - Position of this chunk in the original document
- `similarity_score`: Float - Cosine similarity score between query and chunk
- `query_id`: UUID (Foreign Key) - Links to the query that retrieved this chunk

**Validation Rules**:
- Content must not be empty
- Source URL must be a valid URL format
- Module name must not be empty
- Chunk ID must be non-negative
- Similarity score must be between 0 and 1

## Entity: Response
**Description**: The generated answer with citations to source materials

**Fields**:
- `id`: UUID (Primary Key) - Unique identifier for the response
- `content`: String (Text) - The generated response content
- `citations`: JSON - List of citations with source metadata
- `confidence`: Float (Optional) - Confidence score of the response
- `timestamp`: DateTime - When the response was generated
- `query_id`: UUID (Foreign Key) - Links to the query
- `conversation_id`: UUID (Foreign Key) - Links to the conversation

**Validation Rules**:
- Content must not be empty
- Citations must contain valid source metadata
- Confidence must be between 0 and 1 if provided

## Entity: Conversation
**Description**: A session containing the history of queries and responses

**Fields**:
- `id`: UUID (Primary Key) - Unique identifier for the conversation
- `session_token`: String (Optional) - Session identifier for tracking
- `created_at`: DateTime - When the conversation started
- `updated_at`: DateTime - When the conversation was last updated
- `is_active`: Boolean - Whether the conversation is currently active

**Validation Rules**:
- Created at must be before updated at
- Session token is optional but if provided, must be valid format

## Entity: QueryLog
**Description**: A record of user queries and system responses for analytics

**Fields**:
- `id`: UUID (Primary Key) - Unique identifier for the log entry
- `query_text`: String (Text) - The original query text
- `response_text`: String (Text) - The generated response text
- `retrieved_chunks_count`: Integer - Number of chunks retrieved
- `processing_time_ms`: Integer - Time taken to process the query in milliseconds
- `timestamp`: DateTime - When the query was processed
- `user_agent`: String (Optional) - Client information
- `conversation_id`: UUID (Foreign Key) - Links to the conversation

**Validation Rules**:
- Query text must not be empty
- Processing time must be non-negative
- Retrieved chunks count must be non-negative

## Relationships

- Conversation (1) → Query (Many): A conversation contains multiple queries
- Query (1) → RetrievedChunk (Many): A query can retrieve multiple chunks
- Query (1) → Response (1): A query generates one response
- Conversation (1) → Response (Many): A conversation contains multiple responses
- Conversation (1) → QueryLog (Many): A conversation generates multiple log entries