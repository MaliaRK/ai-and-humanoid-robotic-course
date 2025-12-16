"""
Data validation script for conversation and query log integrity.
This script validates that all conversations and query logs are stored correctly in the database.
"""
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from database.models import Conversation, QueryLog, CitationLog
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_conversation_integrity(db: Session, conversation_id: str) -> Dict[str, Any]:
    """
    Validate the integrity of a conversation and its associated data.

    Args:
        db: Database session
        conversation_id: ID of the conversation to validate

    Returns:
        Dictionary with validation results
    """
    result = {
        "conversation_exists": False,
        "query_logs_count": 0,
        "citation_logs_count": 0,
        "integrity_issues": [],
        "validation_passed": False
    }

    # Check if conversation exists
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        result["integrity_issues"].append(f"Conversation {conversation_id} does not exist")
        return result

    result["conversation_exists"] = True

    # Get query logs for this conversation
    query_logs = db.query(QueryLog).filter(QueryLog.conversation_id == conversation_id).all()
    result["query_logs_count"] = len(query_logs)

    # Validate each query log and its citations
    total_citations = 0
    for query_log in query_logs:
        # Validate query log fields
        if not query_log.query_text:
            result["integrity_issues"].append(f"Query log {query_log.id} has empty query_text")
        if not query_log.response_text:
            result["integrity_issues"].append(f"Query log {query_log.id} has empty response_text")

        # Count and validate citations for this query
        citations = db.query(CitationLog).filter(CitationLog.query_log_id == query_log.id).all()
        total_citations += len(citations)

        for citation in citations:
            # Validate citation fields
            if not citation.source_url:
                result["integrity_issues"].append(f"Citation {citation.id} has empty source_url")
            if not citation.module_name:
                result["integrity_issues"].append(f"Citation {citation.id} has empty module_name")

    result["citation_logs_count"] = total_citations

    # Overall validation
    result["validation_passed"] = len(result["integrity_issues"]) == 0

    if result["validation_passed"]:
        logger.info(f"Conversation {conversation_id} passed integrity validation")
    else:
        logger.warning(f"Conversation {conversation_id} failed integrity validation with {len(result['integrity_issues'])} issues")

    return result

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
    conversations = db.query(Conversation).offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(conversations)} conversations")
    return conversations

def validate_all_conversations(db: Session) -> Dict[str, Any]:
    """
    Validate integrity of all conversations in the database.

    Args:
        db: Database session

    Returns:
        Dictionary with overall validation results
    """
    result = {
        "total_conversations": 0,
        "conversations_with_issues": 0,
        "total_query_logs": 0,
        "total_citation_logs": 0,
        "validation_summary": {}
    }

    # Get all conversations
    all_conversations = get_all_conversations(db)
    result["total_conversations"] = len(all_conversations)

    conversations_with_issues = []

    for conversation in all_conversations:
        validation = validate_conversation_integrity(db, conversation.id)
        result["total_query_logs"] += validation["query_logs_count"]
        result["total_citation_logs"] += validation["citation_logs_count"]

        if not validation["validation_passed"]:
            conversations_with_issues.append({
                "conversation_id": conversation.id,
                "issues": validation["integrity_issues"]
            })

    result["conversations_with_issues"] = len(conversations_with_issues)
    result["validation_summary"] = {
        "conversations_checked": len(all_conversations),
        "conversations_with_issues": len(conversations_with_issues),
        "issues_found": sum(len(c["issues"]) for c in conversations_with_issues)
    }

    logger.info(f"Validated {len(all_conversations)} conversations, {len(conversations_with_issues)} with issues")
    return result