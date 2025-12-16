from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID

# Request Models
class QueryRequest(BaseModel):
    """
    Request model for RAG queries.
    """
    query: str = Field(..., min_length=1, max_length=1000, description="The query text from the user")
    scope: Optional[str] = Field(None, description="Optional scope parameter for scoped queries")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for continuing existing conversation")


class HealthCheckResponse(BaseModel):
    """
    Response model for health check endpoint.
    """
    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(..., description="Timestamp of the health check")
    services: dict = Field(..., description="Status of individual services")


# Response Models
class Citation(BaseModel):
    """
    Model for citations in responses.
    """
    url: str = Field(..., description="URL where the content was found")
    module: str = Field(..., description="Name of the module/chapter")
    chunk_id: int = Field(..., description="Position of this chunk in the original document")
    text_preview: Optional[str] = Field(None, description="Preview of the cited text")


class QueryResponse(BaseModel):
    """
    Response model for RAG queries.
    """
    id: str = Field(..., description="UUID for the response")
    query: str = Field(..., description="The original query text")
    response: str = Field(..., description="The generated response content")
    citations: List[Citation] = Field(..., description="List of citations with source metadata")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score of the response")
    retrieved_chunks_count: int = Field(..., description="Number of chunks retrieved")
    processing_time_ms: int = Field(..., description="Time taken to process the query in milliseconds")
    conversation_id: str = Field(..., description="Identifier for the conversation session")


class ErrorResponse(BaseModel):
    """
    Model for error responses.
    """
    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Detailed error message")
    code: str = Field(..., description="Error code")


class ConversationResponse(BaseModel):
    """
    Response model for conversation history retrieval.
    """
    conversation_id: str = Field(..., description="UUID of the conversation")
    created_at: datetime = Field(..., description="When the conversation started")
    updated_at: datetime = Field(..., description="When the conversation was last updated")
    queries: List[dict] = Field(..., description="List of queries and responses in the conversation")


class RetrievedChunk(BaseModel):
    """
    Model for retrieved content chunks.
    """
    id: str = Field(..., description="UUID for the chunk")
    content: str = Field(..., description="The actual text content of the chunk")
    source_url: str = Field(..., description="URL where the content was found")
    module_name: str = Field(..., description="Name of the module/chapter")
    chunk_id: int = Field(..., description="Position of this chunk in the original document")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity score between query and chunk")