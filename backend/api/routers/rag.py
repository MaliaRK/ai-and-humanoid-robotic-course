from fastapi import APIRouter, HTTPException, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional
import logging
import time
from datetime import datetime
from rag_agent.models import QueryRequest, QueryResponse, ErrorResponse, HealthCheckResponse, ConversationResponse
from rag_agent.agent import get_agent
from rag_agent.utils import generate_conversation_id, generate_response_id
from rag_agent.config import RETRIEVAL_TOP_K, SIMILARITY_THRESHOLD

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create rate limiter for this router
limiter = Limiter(key_func=get_remote_address)

# Create router
router = APIRouter()

@router.post("/rag/query", response_model=QueryResponse)
# @limiter.limit("10/minute")  # 10 requests per minute per IP - temporarily disabled for debugging
async def query_rag(request: Request, query_request: QueryRequest):
    """
    Submit a query to the agentic RAG system and receive a grounded response with citations.
    """
    start_time = time.time()
    performance_metrics = {
        "total_processing_time_ms": 0,
        "retrieval_time_ms": 0,
        "generation_time_ms": 0,
        "validation_time_ms": 0
    }

    try:
        # Additional validation for query parameters
        if not query_request.query or not query_request.query.strip():
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    error="INVALID_QUERY",
                    message="Query text is required and cannot be empty",
                    code="BAD_REQUEST"
                ).dict()
            )

        # Validate query length
        if len(query_request.query.strip()) < 3:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    error="INVALID_QUERY",
                    message="Query must be at least 3 characters long",
                    code="BAD_REQUEST"
                ).dict()
            )

        # Validate scope if provided
        if query_request.scope is not None:
            allowed_scopes = ["course", "modules", "readings", "assignments", "general"]
            if query_request.scope.lower() not in allowed_scopes:
                raise HTTPException(
                    status_code=400,
                    detail=ErrorResponse(
                        error="INVALID_SCOPE",
                        message=f"Invalid scope: {query_request.scope}. Allowed scopes: {allowed_scopes}",
                        code="BAD_REQUEST"
                    ).dict()
                )

        logger.info(f"Processing RAG query: {query_request.query[:50]}...")

        # Use conversation ID from request if provided, otherwise generate a new one
        conversation_id = query_request.conversation_id if query_request.conversation_id else generate_conversation_id()

        # Process the query through the agent with appropriate parameters
        top_k = RETRIEVAL_TOP_K
        similarity_threshold = SIMILARITY_THRESHOLD

        # Adjust parameters based on scope if provided
        if query_request.scope and query_request.scope.lower() == "general":
            # For general queries, we might want to be more permissive
            similarity_threshold = max(0.1, similarity_threshold * 0.8)  # Lower threshold
        elif query_request.scope:
            # For specific scopes, we might want to be more strict
            similarity_threshold = min(0.9, similarity_threshold * 1.2)  # Higher threshold

        # Use the basic query processing without database logging to avoid hangs
        # due to potential database connection issues
        agent_orchestrator = get_agent()
        result = agent_orchestrator.process_query(
            query=query_request.query,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
        # Add conversation ID to result if not present
        if "conversation_id" not in result:
            result["conversation_id"] = conversation_id

        # Calculate processing time in milliseconds
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Calculate a more meaningful confidence score based on various factors
        retrieved_count = result.get("retrieved_chunks_count", 0)
        is_grounded = result.get("grounded_in_retrieved_content", False)
        citation_accuracy = result.get("citation_accuracy_validated", False)
        has_valid_citations = result.get("has_valid_citations", False)

        # Calculate confidence based on retrieved content and grounding validation
        base_confidence = 0.5  # Base confidence
        if retrieved_count > 0:
            base_confidence += 0.3  # Boost for having retrieved content
        if is_grounded:
            base_confidence += 0.2  # Additional boost for being grounded in content
        if has_valid_citations:
            base_confidence += 0.1  # Additional boost for valid citations
        if retrieved_count >= 3:  # If we have multiple sources
            base_confidence += 0.1

        confidence_score = min(1.0, base_confidence)  # Cap at 1.0

        # Create response object
        response = QueryResponse(
            id=generate_response_id(),
            query=query_request.query,
            response=result.get("response", ""),
            citations=result.get("citations", []),
            confidence=confidence_score,
            retrieved_chunks_count=retrieved_count,
            processing_time_ms=processing_time_ms,
            conversation_id=result.get("conversation_id", conversation_id)
        )

        logger.info(f"Query processed successfully in {processing_time_ms}ms")
        return response

    except HTTPException:
        # Re-raise HTTP exceptions as they're already properly formatted
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing RAG query: {e}")
        error_response = ErrorResponse(
            error="INTERNAL_SERVER_ERROR",
            message="An internal server error occurred while processing your query",
            code="INTERNAL_ERROR"
        )
        raise HTTPException(status_code=500, detail=error_response.dict())

@router.get("/rag/health", response_model=HealthCheckResponse)
@limiter.limit("30/minute")  # Health checks are lightweight, allow more frequent calls
async def health_check(request: Request):
    """
    Check the health status of the RAG system and its dependencies.
    """
    import requests
    from qdrant_client import QdrantClient
    from rag_agent.config import validate_environment

    timestamp = datetime.now()

    # Validate environment
    env_ok, missing_vars = validate_environment()

    services_status = {
        "agent": "healthy" if env_ok else "unhealthy",
        "qdrant": "checking...",
        "gemini": "checking...",
        "database": "checking..."
    }

    # Check Qdrant connection
    try:
        from retrieval.client import get_qdrant_client
        qdrant_client = get_qdrant_client()
        # Try to get collections to verify connection
        qdrant_client.get_collections()
        services_status["qdrant"] = "healthy"
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        services_status["qdrant"] = "unhealthy"

    # Check Gemini (just verify API key is available)
    import os
    if os.getenv("GEMINI_API_KEY"):
        services_status["gemini"] = "healthy"
    else:
        services_status["gemini"] = "unhealthy"

    # Check database connection
    try:
        from sqlalchemy import text
        from database.session import get_engine
        engine = get_engine()
        # Try to connect and execute a simple query
        with engine.connect() as conn:
            # Execute a simple query to test the connection
            result = conn.execute(text("SELECT 1"))
            services_status["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        services_status["database"] = "unhealthy"

    # Overall status
    all_healthy = all(status == "healthy" for status in services_status.values())
    overall_status = "healthy" if all_healthy else "unhealthy"

    health_response = HealthCheckResponse(
        status=overall_status,
        timestamp=timestamp,
        services=services_status
    )

    return health_response

@router.get("/rag/conversations/{conversation_id}", response_model=ConversationResponse)
@limiter.limit("20/minute")  # Conversation retrieval is database intensive, moderate limit
async def get_conversation(conversation_id: str, request: Request):
    """
    Retrieve conversation history for debugging and analytics.
    """
    from database.session import get_db, get_conversation_with_queries
    from contextlib import contextmanager

    logger.info(f"Retrieving conversation: {conversation_id}")

    # Get database session
    db_gen = get_db()
    db = next(db_gen)

    try:
        # Get conversation with its queries from the database
        db_conversation = get_conversation_with_queries(db, conversation_id)

        if not db_conversation:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(
                    error="CONVERSATION_NOT_FOUND",
                    message=f"Conversation with ID {conversation_id} not found",
                    code="NOT_FOUND"
                ).dict()
            )

        # Format the response
        queries_data = []
        for query_log in db_conversation.queries:
            query_data = {
                "id": query_log.id,
                "query": query_log.query_text,
                "response": query_log.response_text,
                "timestamp": query_log.created_at,
                "processing_time_ms": query_log.processing_time_ms,
                "citations": []  # We can extend this to include citation data if needed
            }

            # Add citation data if available
            for citation in query_log.citations:
                query_data["citations"].append({
                    "url": citation.source_url,
                    "module": citation.module_name,
                    "chunk_id": citation.chunk_id,
                    "text_preview": citation.text_preview,
                    "similarity_score": citation.similarity_score
                })

            queries_data.append(query_data)

        conversation_response = ConversationResponse(
            conversation_id=db_conversation.id,
            created_at=db_conversation.created_at,
            updated_at=db_conversation.updated_at,
            queries=queries_data
        )

        logger.info(f"Successfully retrieved conversation with {len(queries_data)} queries")
        return conversation_response

    except HTTPException:
        # Re-raise HTTP exceptions as they're already properly formatted
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="INTERNAL_SERVER_ERROR",
                message="An error occurred while retrieving the conversation",
                code="INTERNAL_ERROR"
            ).dict()
        )
    finally:
        # Close the database session
        db.close()

# Additional endpoints can be added here as needed