from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID


# Base schemas
class ConversationBase(BaseModel):
    metadata_info: Optional[Dict[str, Any]] = Field(default_factory=dict)


class QueryLogBase(BaseModel):
    conversation_id: str
    query_text: str
    response_text: str
    query_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    response_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    processing_time_ms: Optional[int] = None


class CitationLogBase(BaseModel):
    query_log_id: str
    source_url: str
    module_name: str
    chunk_id: int
    text_preview: Optional[str] = None
    similarity_score: Optional[float] = None


# Create schemas
class ConversationCreate(ConversationBase):
    pass


class QueryLogCreate(QueryLogBase):
    pass


class CitationLogCreate(CitationLogBase):
    pass


# Response schemas (with IDs and timestamps)
class Conversation(ConversationBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CitationLog(CitationLogBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class QueryLog(QueryLogBase):
    id: str
    created_at: datetime
    citations: List[CitationLog] = []

    class Config:
        from_attributes = True


# Extended schemas
class ConversationWithQueries(Conversation):
    queries: List[QueryLog] = []

    class Config:
        from_attributes = True


class QueryLogWithCitations(QueryLog):
    citations: List[CitationLog] = []

    class Config:
        from_attributes = True