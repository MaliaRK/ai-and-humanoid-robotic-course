from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
import logging
import os
import time
from sentence_transformers import SentenceTransformer
from rag_agent.config import QDRANT_COLLECTION_NAME, RETRIEVAL_TOP_K, SIMILARITY_THRESHOLD

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def embed_query(query: str) -> List[float]:
    """
    Generate embedding for a query using local sentence transformer model.

    Args:
        query: The query text to embed

    Returns:
        List of floats representing the embedding vector
    """
    try:
        # Initialize the sentence transformer model
        model = SentenceTransformer('all-MiniLM-L6-v2')

        # Generate embedding using local model
        embedding = model.encode([query])[0].tolist()
        logger.info(f"Generated embedding for query: {query[:50]}...")
        return embedding
    except Exception as e:
        logger.error(f"Error generating embedding for query: {e}")
        raise

def search_similar_chunks(
    qdrant_client: QdrantClient,
    query: str,
    collection_name: str = QDRANT_COLLECTION_NAME,
    top_k: int = RETRIEVAL_TOP_K,
    similarity_threshold: float = SIMILARITY_THRESHOLD
) -> List[Dict[str, Any]]:
    """
    Search for similar content chunks in Qdrant based on the query.

    Args:
        qdrant_client: Initialized Qdrant client
        query: The search query
        collection_name: Name of the Qdrant collection to search
        top_k: Number of top results to retrieve
        similarity_threshold: Minimum similarity score for inclusion

    Returns:
        List of retrieved chunks with metadata
    """
    try:
        # Generate embedding for the query
        query_embedding = embed_query(query)

        # Perform semantic search in Qdrant
        search_results = qdrant_client.query_points(
            collection_name=collection_name,
            query=query_embedding,
            limit=top_k,
            score_threshold=similarity_threshold,
            with_payload=True
        )

        # Format results for easier consumption
        formatted_results = []
        for result in search_results.points:
            formatted_results.append({
                "id": result.id,
                "content": result.payload.get("content", result.payload.get("text", "")) if result.payload else "",
                "source_url": result.payload.get("source_url", result.payload.get("url", "")) if result.payload else "",
                "module_name": result.payload.get("module_name", "") if result.payload else "",
                "chunk_id": result.payload.get("chunk_id", result.payload.get("chunk_index", 0)) if result.payload else 0,
                "similarity_score": result.score,
                "metadata": result.payload  # Include all metadata
            })

        logger.info(f"Found {len(formatted_results)} similar chunks for query: {query[:50]}...")
        return formatted_results

    except Exception as e:
        logger.error(f"Error during semantic search: {e}")
        # Return empty list if search fails
        return []

def search_chunks_by_metadata(
    qdrant_client: QdrantClient,
    metadata_filters: Dict[str, Any],
    collection_name: str = QDRANT_COLLECTION_NAME,
    top_k: int = RETRIEVAL_TOP_K
) -> List[Dict[str, Any]]:
    """
    Search for chunks based on metadata filters.

    Args:
        qdrant_client: Initialized Qdrant client
        metadata_filters: Dictionary of metadata fields to filter by
        collection_name: Name of the Qdrant collection to search
        top_k: Number of top results to retrieve

    Returns:
        List of retrieved chunks with metadata
    """
    try:
        # Create filter conditions based on metadata
        filter_conditions = []
        for key, value in metadata_filters.items():
            filter_conditions.append(
                models.FieldCondition(
                    key=key,
                    match=models.MatchValue(value=value)
                )
            )

        if not filter_conditions:
            return []

        # Create the filter
        search_filter = models.Filter(
            must=filter_conditions
        )

        # Perform search with metadata filters
        search_results = qdrant_client.query_points(
            collection_name=collection_name,
            query_filter=search_filter,
            limit=top_k,
            with_payload=True
        )

        # Format results
        formatted_results = []
        for result in search_results.points:
            formatted_results.append({
                "id": result.id,
                "content": result.payload.get("content", result.payload.get("text", "")) if result.payload else "",
                "source_url": result.payload.get("source_url", result.payload.get("url", "")) if result.payload else "",
                "module_name": result.payload.get("module_name", "") if result.payload else "",
                "chunk_id": result.payload.get("chunk_id", result.payload.get("chunk_index", 0)) if result.payload else 0,
                "similarity_score": result.score,
                "metadata": result.payload
            })

        logger.info(f"Found {len(formatted_results)} chunks by metadata filter")
        return formatted_results

    except Exception as e:
        logger.error(f"Error during metadata search: {e}")
        return []

def validate_retrieved_content(retrieved_chunks: List[Dict[str, Any]], query: str) -> bool:
    """
    Validate that the retrieved content is relevant to the query.

    Args:
        retrieved_chunks: List of retrieved chunks
        query: The original query

    Returns:
        bool: True if content is relevant, False otherwise
    """
    if not retrieved_chunks:
        logger.warning("No chunks retrieved for validation")
        return False

    # Basic validation: check if chunks have required fields
    for chunk in retrieved_chunks:
        required_fields = ["content", "source_url", "module_name", "chunk_id", "similarity_score"]
        for field in required_fields:
            if field not in chunk or chunk[field] is None:
                logger.warning(f"Missing required field '{field}' in chunk: {chunk.get('id', 'unknown')}")
                return False

    # Check similarity scores are within expected range
    for chunk in retrieved_chunks:
        if not (0.0 <= chunk.get("similarity_score", 0.0) <= 1.0):
            logger.warning(f"Invalid similarity score: {chunk.get('similarity_score', 0.0)}")
            return False

    logger.info(f"Successfully validated {len(retrieved_chunks)} retrieved chunks")
    return True