import os
from typing import Generator, Optional
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from rag_agent.config import validate_environment
from .models import Conversation, QueryLog, CitationLog
from .schemas import ConversationCreate, QueryLogCreate, CitationLogCreate
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Validate environment before initializing database connection
is_valid, missing_vars = validate_environment()
if not is_valid:
    raise EnvironmentError(f"Missing required environment variables: {missing_vars}")

# Get database URL from environment
DATABASE_URL = os.getenv("NEON_DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("NEON_DATABASE_URL environment variable is not set")

# Create engine with connection pooling configuration
engine = create_engine(
    DATABASE_URL,
    pool_size=10,  # Default from environment or 10
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,  # Recycle connections every 5 minutes
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db() -> Generator:
    """
    Dependency function to get database session.

    Yields:
        Session: Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_engine():
    """
    Get the SQLAlchemy engine instance.

    Returns:
        Engine: SQLAlchemy engine
    """
    return engine

def create_conversation(db: Session, conversation: ConversationCreate) -> Conversation:
    """
    Create a new conversation in the database.

    Args:
        db: Database session
        conversation: ConversationCreate schema with conversation data

    Returns:
        Created Conversation object
    """
    from datetime import datetime
    db_conversation = Conversation(
        metadata_info=conversation.metadata_info
    )
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    logger.info(f"Created conversation with ID: {db_conversation.id}")
    return db_conversation

def get_conversation(db: Session, conversation_id: str) -> Optional[Conversation]:
    """
    Retrieve a conversation by ID from the database.

    Args:
        db: Database session
        conversation_id: ID of the conversation to retrieve

    Returns:
        Conversation object if found, None otherwise
    """
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation:
        logger.info(f"Retrieved conversation with ID: {conversation_id}")
    else:
        logger.info(f"Conversation with ID {conversation_id} not found")
    return conversation

def update_conversation(db: Session, conversation_id: str, metadata_info: dict) -> Optional[Conversation]:
    """
    Update a conversation's metadata in the database.

    Args:
        db: Database session
        conversation_id: ID of the conversation to update
        metadata_info: New metadata to update

    Returns:
        Updated Conversation object if found, None otherwise
    """
    from datetime import datetime
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation:
        conversation.metadata_info = metadata_info
        conversation.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(conversation)
        logger.info(f"Updated conversation with ID: {conversation_id}")
    return conversation

def delete_conversation(db: Session, conversation_id: str) -> bool:
    """
    Delete a conversation from the database.

    Args:
        db: Database session
        conversation_id: ID of the conversation to delete

    Returns:
        True if deletion was successful, False otherwise
    """
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation:
        db.delete(conversation)
        db.commit()
        logger.info(f"Deleted conversation with ID: {conversation_id}")
        return True
    return False

def create_query_log(db: Session, query_log: QueryLogCreate) -> QueryLog:
    """
    Create a new query log in the database.

    Args:
        db: Database session
        query_log: QueryLogCreate schema with query log data

    Returns:
        Created QueryLog object
    """
    db_query_log = QueryLog(
        conversation_id=query_log.conversation_id,
        query_text=query_log.query_text,
        response_text=query_log.response_text,
        query_metadata=query_log.query_metadata,
        response_metadata=query_log.response_metadata,
        processing_time_ms=query_log.processing_time_ms
    )
    db.add(db_query_log)
    db.commit()
    db.refresh(db_query_log)
    logger.info(f"Created query log with ID: {db_query_log.id} for conversation: {query_log.conversation_id}")
    return db_query_log

def create_citation_log(db: Session, citation_log: CitationLogCreate) -> CitationLog:
    """
    Create a new citation log in the database.

    Args:
        db: Database session
        citation_log: CitationLogCreate schema with citation log data

    Returns:
        Created CitationLog object
    """
    db_citation_log = CitationLog(
        query_log_id=citation_log.query_log_id,
        source_url=citation_log.source_url,
        module_name=citation_log.module_name,
        chunk_id=citation_log.chunk_id,
        text_preview=citation_log.text_preview,
        similarity_score=citation_log.similarity_score
    )
    db.add(db_citation_log)
    db.commit()
    db.refresh(db_citation_log)
    logger.info(f"Created citation log with ID: {db_citation_log.id} for query log: {citation_log.query_log_id}")
    return db_citation_log

def get_query_logs_by_conversation(db: Session, conversation_id: str) -> list[QueryLog]:
    """
    Retrieve all query logs for a specific conversation.

    Args:
        db: Database session
        conversation_id: ID of the conversation

    Returns:
        List of QueryLog objects
    """
    from sqlalchemy.orm import joinedload

    # Use joinedload to optimize the query and include citations in the same query
    query_logs = db.query(QueryLog)\
        .options(joinedload(QueryLog.citations))\
        .filter(QueryLog.conversation_id == conversation_id)\
        .order_by(QueryLog.created_at.desc()).all()  # Order by creation time, newest first

    logger.info(f"Retrieved {len(query_logs)} query logs for conversation: {conversation_id}")
    return query_logs

def get_conversation_with_queries(db: Session, conversation_id: str) -> Optional[Conversation]:
    """
    Retrieve a conversation with all its associated query logs.

    Args:
        db: Database session
        conversation_id: ID of the conversation to retrieve

    Returns:
        Conversation object with queries if found, None otherwise
    """
    from sqlalchemy.orm import joinedload

    # Use joinedload to optimize the query and avoid N+1 query problem
    conversation = db.query(Conversation)\
        .options(joinedload(Conversation.queries).joinedload(QueryLog.citations))\
        .filter(Conversation.id == conversation_id).first()

    if conversation:
        logger.info(f"Retrieved conversation with ID: {conversation_id} and {len(conversation.queries)} queries")
    return conversation

def get_recent_conversations(db: Session, limit: int = 50) -> list[Conversation]:
    """
    Retrieve recent conversations efficiently.

    Args:
        db: Database session
        limit: Maximum number of records to return

    Returns:
        List of Conversation objects, ordered by most recent
    """
    conversations = db.query(Conversation)\
        .order_by(Conversation.created_at.desc())\
        .limit(limit).all()
    logger.info(f"Retrieved {len(conversations)} recent conversations")
    return conversations

def get_all_conversations(db: Session, skip: int = 0, limit: int = 100) -> list[Conversation]:
    """
    Retrieve all conversations with optional pagination.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of Conversation objects
    """
    conversations = db.query(Conversation)\
        .offset(skip)\
        .limit(limit)\
        .order_by(Conversation.created_at.desc()).all()
    logger.info(f"Retrieved {len(conversations)} conversations")
    return conversations