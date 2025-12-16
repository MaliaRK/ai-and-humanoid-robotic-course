from typing import List, Dict, Any, Optional
from openai import OpenAI
import logging
from pydantic import BaseModel
from .openai_client import get_openai_client
from .gemini_client import get_gemini_model
from .tools import call_retrieval_tool
from .config import AGENT_MODEL, AGENT_TEMPERATURE, MAX_RETRIEVAL_CHUNKS
from .utils import retry_with_backoff, format_error_response, validate_response_content
from .models import RetrievedChunk

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """
    Orchestrates the agent to perform retrieval and generation.
    """
    def __init__(self):
        self.openai_client = get_openai_client()
        self.gemini_model = get_gemini_model()
        self.agent_model = AGENT_MODEL
        self.temperature = AGENT_TEMPERATURE

    @retry_with_backoff(max_retries=3)
    def retrieve_content(self, query: str, top_k: int = 5, similarity_threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        Retrieve content from the knowledge base based on the query.

        Args:
            query: The search query
            top_k: Number of top results to retrieve
            similarity_threshold: Minimum similarity score for inclusion

        Returns:
            List of retrieved chunks with metadata
        """
        try:
            # Validate inputs
            if not query or not query.strip():
                logger.warning("Empty query provided to retrieve_content")
                return []

            if top_k <= 0:
                logger.warning(f"Invalid top_k value: {top_k}, using default 5")
                top_k = 5

            if not (0.0 <= similarity_threshold <= 1.0):
                logger.warning(f"Invalid similarity_threshold: {similarity_threshold}, using default 0.3")
                similarity_threshold = 0.3

            logger.info(f"Retrieving content for query: {query[:50]}...")

            # Use the retrieval tool to get relevant chunks
            retrieved_chunks = call_retrieval_tool(
                query=query,
                top_k=top_k,
                similarity_threshold=similarity_threshold
            )

            logger.info(f"Retrieved {len(retrieved_chunks)} chunks")
            return retrieved_chunks

        except Exception as e:
            logger.error(f"Error retrieving content: {e}")
            # Return empty list but log the error for monitoring
            return []

    @retry_with_backoff(max_retries=3)
    def generate_response_with_gemini(self, query: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """
        Generate a response using Gemini based on the query and retrieved content.

        Args:
            query: The original query
            retrieved_chunks: List of retrieved chunks with metadata

        Returns:
            Generated response string
        """
        logger.info(f"Generating response with Gemini for query: {query[:50]}...")

        # Format the context from retrieved chunks
        context = ""
        for i, chunk in enumerate(retrieved_chunks):
            context += f"Context {i+1}:\n"
            context += f"Content: {chunk.get('content', '')}\n"
            context += f"Source: {chunk.get('source_url', '')}\n"
            context += f"Module: {chunk.get('module_name', '')}\n"
            context += f"Similarity Score: {chunk.get('similarity_score', 0.0)}\n\n"

        # Create the prompt for Gemini
        prompt = f"""
        You are an AI assistant for the AI & Humanoid Robotics course. Answer the user's query based strictly on the provided context.

        Query: {query}

        Context:
        {context}

        Instructions:
        1. Answer the query based only on the provided context
        2. If the context doesn't contain information to answer the query, say "I couldn't find relevant information in the provided content to answer your query."
        3. Provide specific citations to the source materials when possible
        4. Be concise but comprehensive in your response
        5. If multiple sources contain relevant information, synthesize them appropriately
        """

        try:
            # Generate response using Gemini
            response = self.gemini_model.generate_content(prompt)
            generated_text = response.text

            # Validate the response content
            is_valid, error_msg = validate_response_content(generated_text)
            if not is_valid:
                logger.error(f"Invalid response content: {error_msg}")
                return f"Error generating response: {error_msg}"

            logger.info(f"Generated response with {len(generated_text)} characters")
            return generated_text

        except Exception as e:
            logger.error(f"Error generating response with Gemini: {e}")
            # Instead of failing completely, provide a graceful fallback
            if retrieved_chunks:
                # If we have retrieved content but Gemini failed, return a summary of the content
                fallback_response = f"I found some relevant information but couldn't generate a complete response. Here's what I found:\n\n"
                for i, chunk in enumerate(retrieved_chunks[:3]):  # Show top 3 chunks
                    fallback_response += f"Source: {chunk.get('source_url', 'Unknown')}\n"
                    fallback_response += f"Content: {chunk.get('content', '')[:200]}...\n\n"
                return fallback_response
            else:
                return "I'm sorry, but I couldn't find relevant information to answer your query."

    def validate_response_grounding(self, response: str, retrieved_chunks: List[Dict[str, Any]]) -> bool:
        """
        Validate that the response is grounded in the retrieved content.

        Args:
            response: The generated response
            retrieved_chunks: The chunks used to generate the response

        Returns:
            bool: True if response is grounded in retrieved content, False otherwise
        """
        if not retrieved_chunks:
            logger.warning("No retrieved chunks to validate against")
            return False

        # Basic validation: check if response contains content that relates to the retrieved chunks
        response_lower = response.lower()
        has_connection = False

        for chunk in retrieved_chunks:
            chunk_content = chunk.get('content', '').lower()
            # Check if there's some overlap in content
            if len(chunk_content) > 10:  # Only check meaningful chunks
                # Simple keyword overlap check
                chunk_words = set(chunk_content.split()[:20])  # Check first 20 words
                response_words = set(response_lower.split())

                common_words = chunk_words.intersection(response_words)
                if len(common_words) > 0:  # If there's at least some overlap
                    has_connection = True
                    break

        if not has_connection:
            logger.warning("Response doesn't appear to be grounded in retrieved content")
            return False

        logger.info("Response validation passed - content is grounded in retrieved chunks")
        return True

    def validate_citation_accuracy(self, citations: List[Dict[str, Any]], retrieved_chunks: List[Dict[str, Any]]) -> bool:
        """
        Validate that citations accurately reflect the retrieved content metadata.

        Args:
            citations: List of citations to validate
            retrieved_chunks: The original retrieved chunks

        Returns:
            bool: True if all citations have accurate metadata, False otherwise
        """
        if not citations:
            logger.info("No citations to validate")
            return True

        # Create a mapping of retrieved chunks by their ID for easy lookup
        chunk_map = {chunk.get('id'): chunk for chunk in retrieved_chunks if chunk.get('id')}

        # If no IDs are available, try to match by other metadata
        if not chunk_map:
            chunk_map = {}
            for chunk in retrieved_chunks:
                key = (chunk.get('source_url', ''), chunk.get('module_name', ''), chunk.get('chunk_id', 0))
                chunk_map[key] = chunk

        for citation in citations:
            # Check if citation has required fields
            required_fields = ['url', 'module', 'chunk_id']
            for field in required_fields:
                if field not in citation:
                    logger.error(f"Missing required field '{field}' in citation")
                    return False

            # Try to find matching chunk in retrieved content
            matching_chunk = None
            for chunk in retrieved_chunks:
                if (chunk.get('source_url', '') == citation['url'] and
                    chunk.get('module_name', '') == citation['module'] and
                    chunk.get('chunk_id', 0) == citation['chunk_id']):
                    matching_chunk = chunk
                    break

            if not matching_chunk:
                logger.error(f"No matching chunk found for citation: {citation}")
                return False

            # Validate that citation content matches retrieved content
            citation_preview = citation.get('text_preview', '')
            if citation_preview and matching_chunk.get('content', ''):
                # Check if the preview is a substring of the actual content
                if citation_preview not in matching_chunk['content']:
                    logger.warning(f"Citation preview doesn't match content: {citation_preview[:50]}...")

        logger.info(f"Citation validation passed for {len(citations)} citations")
        return True

    def process_query(self, query: str, top_k: int = 5, similarity_threshold: float = 0.3) -> Dict[str, Any]:
        """
        Process a query through the full agent pipeline: retrieval -> generation -> validation.

        Args:
            query: The user's query
            top_k: Number of top results to retrieve
            similarity_threshold: Minimum similarity score for inclusion

        Returns:
            Dictionary containing the response and metadata
        """
        try:
            logger.info(f"Processing query: {query[:50]}...")

            # Step 1: Retrieve relevant content
            retrieved_chunks = self.retrieve_content(
                query=query,
                top_k=top_k,
                similarity_threshold=similarity_threshold
            )

            if not retrieved_chunks:
                logger.warning(f"No relevant content found for query: {query}")
                return {
                    "response": "I couldn't find relevant information in the provided content to answer your query.",
                    "citations": [],
                    "retrieved_chunks_count": 0,
                    "grounded_in_retrieved_content": False
                }

            # Step 2: Generate response based on retrieved content
            generated_response = self.generate_response_with_gemini(
                query=query,
                retrieved_chunks=retrieved_chunks
            )

            # Step 3: Validate that response is grounded in retrieved content
            is_grounded = self.validate_response_grounding(
                response=generated_response,
                retrieved_chunks=retrieved_chunks
            )

            # Format citations
            citations = []
            for chunk in retrieved_chunks:
                citations.append({
                    "url": chunk.get("source_url", ""),
                    "module": chunk.get("module_name", ""),
                    "chunk_id": chunk.get("chunk_id", 0),
                    "text_preview": chunk.get("content", "")[:100] + "..." if len(chunk.get("content", "")) > 100 else chunk.get("content", "")
                })

            # Validate citation accuracy
            citation_accuracy = self.validate_citation_accuracy(citations, retrieved_chunks)

            # Validate that citations are present when content was retrieved
            has_valid_citations = len(citations) > 0 if len(retrieved_chunks) > 0 else True

            result = {
                "response": generated_response,
                "citations": citations,
                "retrieved_chunks_count": len(retrieved_chunks),
                "grounded_in_retrieved_content": is_grounded,
                "citation_accuracy_validated": citation_accuracy,
                "has_valid_citations": has_valid_citations
            }

            logger.info(f"Successfully processed query. Retrieved {len(retrieved_chunks)} chunks, grounded: {is_grounded}, citation accuracy validated: {citation_accuracy}, has valid citations: {has_valid_citations}")
            return result

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "response": f"An error occurred while processing your query: {str(e)}",
                "citations": [],
                "retrieved_chunks_count": 0,
                "grounded_in_retrieved_content": False,
                "error": str(e)
            }

    def process_query_with_logging(self, query: str, conversation_id: str = None, top_k: int = 5, similarity_threshold: float = 0.3) -> Dict[str, Any]:
        """
        Process a query and log it to the database with conversation tracking.

        Args:
            query: The user's query
            conversation_id: Existing conversation ID (if any)
            top_k: Number of top results to retrieve
            similarity_threshold: Minimum similarity score for inclusion

        Returns:
            Dictionary containing the response and metadata
        """
        from database.session import get_db, create_conversation, create_query_log, create_citation_log
        from database.schemas import ConversationCreate, QueryLogCreate, CitationLogCreate
        from contextlib import contextmanager

        # Get database session
        db_gen = get_db()
        db = next(db_gen)

        try:
            # Create or use existing conversation
            if not conversation_id:
                # Create a new conversation
                conversation_data = ConversationCreate(metadata_info={})
                conversation = create_conversation(db, conversation_data)
                conversation_id = conversation.id
            else:
                # Verify conversation exists
                from database.session import get_conversation
                existing_conversation = get_conversation(db, conversation_id)
                if not existing_conversation:
                    # Create new conversation if ID doesn't exist
                    conversation_data = ConversationCreate(metadata_info={})
                    conversation = create_conversation(db, conversation_data)
                    conversation_id = conversation.id

            # Process the query
            result = self.process_query(query, top_k, similarity_threshold)

            # Log the query to the database
            query_log_data = QueryLogCreate(
                conversation_id=conversation_id,
                query_text=query,
                response_text=result.get("response", ""),
                query_metadata={"top_k": top_k, "similarity_threshold": similarity_threshold},
                response_metadata={
                    "retrieved_chunks_count": result.get("retrieved_chunks_count", 0),
                    "grounded_in_retrieved_content": result.get("grounded_in_retrieved_content", False),
                    "citation_accuracy_validated": result.get("citation_accuracy_validated", False),
                    "confidence": result.get("confidence", 0.0)
                },
                processing_time_ms=result.get("processing_time_ms", 0)
            )
            query_log = create_query_log(db, query_log_data)

            # Log citations if they exist
            citations = result.get("citations", [])
            for citation in citations:
                citation_log_data = CitationLogCreate(
                    query_log_id=query_log.id,
                    source_url=citation.get("url", ""),
                    module_name=citation.get("module", ""),
                    chunk_id=citation.get("chunk_id", 0),
                    text_preview=citation.get("text_preview", ""),
                    similarity_score=citation.get("similarity_score")
                )
                create_citation_log(db, citation_log_data)

            # Add conversation ID to result
            result["conversation_id"] = conversation_id

            logger.info(f"Query processed and logged for conversation: {conversation_id}")
            return result

        finally:
            # Close the database session
            db.close()

# Global agent instance
agent_orchestrator = AgentOrchestrator()

def get_agent():
    """
    Get the agent orchestrator instance.

    Returns:
        AgentOrchestrator: The agent orchestrator instance
    """
    return agent_orchestrator

def run_agent_query(query: str, top_k: int = 5, similarity_threshold: float = 0.3, conversation_id: str = None) -> Dict[str, Any]:
    """
    Run a query through the agent pipeline with optional conversation tracking.

    Args:
        query: The user's query
        top_k: Number of top results to retrieve
        similarity_threshold: Minimum similarity score for inclusion
        conversation_id: Existing conversation ID (if any)

    Returns:
        Dictionary containing the response and metadata
    """
    return agent_orchestrator.process_query_with_logging(query, conversation_id, top_k, similarity_threshold)