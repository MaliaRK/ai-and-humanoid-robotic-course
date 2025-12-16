from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class Conversation(Base):
    """
    SQLAlchemy model for conversation history.
    """
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    metadata_info = Column(JSON, default={})  # Additional metadata about the conversation

    # Relationship to query logs
    queries = relationship("QueryLog", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Conversation(id={self.id}, created_at={self.created_at})>"


class QueryLog(Base):
    """
    SQLAlchemy model for query logs.
    """
    __tablename__ = "query_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    query_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=False)
    query_metadata = Column(JSON, default={})  # Additional metadata about the query
    response_metadata = Column(JSON, default={})  # Metadata about the response (confidence, etc.)
    processing_time_ms = Column(Integer, nullable=True)  # Processing time in milliseconds
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to conversation
    conversation = relationship("Conversation", back_populates="queries")

    def __repr__(self):
        return f"<QueryLog(id={self.id}, conversation_id={self.conversation_id}, created_at={self.created_at})>"


class CitationLog(Base):
    """
    SQLAlchemy model for citation logs, linking to specific query logs.
    """
    __tablename__ = "citation_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    query_log_id = Column(String(36), ForeignKey("query_logs.id"), nullable=False)
    source_url = Column(String(500), nullable=False)
    module_name = Column(String(200), nullable=False)
    chunk_id = Column(Integer, nullable=False)
    text_preview = Column(Text, nullable=True)
    similarity_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to query log
    query_log = relationship("QueryLog", back_populates="citations")

    def __repr__(self):
        return f"<CitationLog(id={self.id}, query_log_id={self.query_log_id}, source_url={self.source_url})>"


# Add relationship to QueryLog
QueryLog.citations = relationship("CitationLog", back_populates="query_log", cascade="all, delete-orphan")