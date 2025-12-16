from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models
from pydantic import BaseModel
import logging
from .config import QDRANT_COLLECTION_NAME, RETRIEVAL_TOP_K, SIMILARITY_THRESHOLD
from .gemini_client import get_gemini_model
from retrieval.client import get_qdrant_client
from retrieval.search import search_similar_chunks

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RetrievalTool(BaseModel):
    """
    Tool for retrieving information from the Qdrant vector database.
    """
    name: str = "retrieve_information"
    description: str = "Retrieve relevant information from the knowledge base based on the provided query"

    class ToolInput(BaseModel):
        query: str
        top_k: int = RETRIEVAL_TOP_K
        similarity_threshold: float = SIMILARITY_THRESHOLD

    def execute(self, query: str, top_k: int = RETRIEVAL_TOP_K, similarity_threshold: float = SIMILARITY_THRESHOLD) -> List[Dict[str, Any]]:
        """
        Execute the retrieval tool to find relevant information based on the query.

        Args:
            query: The search query
            top_k: Number of top results to retrieve
            similarity_threshold: Minimum similarity score for inclusion

        Returns:
            List of retrieved chunks with metadata
        """
        try:
            # Get Qdrant client
            qdrant_client = get_qdrant_client()

            # Perform semantic search
            results = search_similar_chunks(
                qdrant_client=qdrant_client,
                query=query,
                collection_name=QDRANT_COLLECTION_NAME,
                top_k=top_k,
                similarity_threshold=similarity_threshold
            )

            logger.info(f"Retrieved {len(results)} chunks for query: {query[:50]}...")

            return results

        except Exception as e:
            logger.error(f"Error in retrieval tool: {e}")
            # Re-raise the exception to trigger retry logic in the agent
            raise

# Create a global instance of the retrieval tool
retrieval_tool = RetrievalTool()

def get_retrieval_tool():
    """
    Get the retrieval tool instance.

    Returns:
        RetrievalTool: The retrieval tool instance
    """
    return retrieval_tool

def call_retrieval_tool(query: str, top_k: int = RETRIEVAL_TOP_K, similarity_threshold: float = SIMILARITY_THRESHOLD) -> List[Dict[str, Any]]:
    """
    Call the retrieval tool directly.

    Args:
        query: The search query
        top_k: Number of top results to retrieve
        similarity_threshold: Minimum similarity score for inclusion

    Returns:
        List of retrieved chunks with metadata
    """
    return retrieval_tool.execute(query, top_k, similarity_threshold)