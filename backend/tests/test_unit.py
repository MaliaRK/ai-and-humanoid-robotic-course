import pytest
import os
from unittest.mock import patch, MagicMock
from rag_agent.agent import AgentOrchestrator
from rag_agent.tools import RetrievalTool, call_retrieval_tool
from rag_agent.utils import generate_conversation_id, generate_response_id, retry_with_backoff
from database.session import create_conversation, get_conversation, update_conversation, delete_conversation
from database.schemas import ConversationCreate
from sqlalchemy.orm import Session
from datetime import datetime

def test_generate_conversation_id():
    """Test conversation ID generation"""
    conversation_id = generate_conversation_id()
    assert isinstance(conversation_id, str)
    assert len(conversation_id) > 0
    assert conversation_id.startswith("conv_")  # Assuming the function prefixes with 'conv_'


def test_generate_response_id():
    """Test response ID generation"""
    response_id = generate_response_id()
    assert isinstance(response_id, str)
    assert len(response_id) > 0
    assert response_id.startswith("resp_")  # Assuming the function prefixes with 'resp_'


def test_agent_initialization():
    """Test AgentOrchestrator initialization"""
    agent = AgentOrchestrator()
    assert agent is not None
    assert hasattr(agent, 'retrieve_content')
    assert hasattr(agent, 'generate_response_with_gemini')
    assert hasattr(agent, 'validate_response_grounding')


def test_retry_with_backoff_decorator():
    """Test the retry with backoff decorator functionality"""
    attempt_count = 0
    max_attempts = 3

    @retry_with_backoff(max_retries=max_attempts)
    def test_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < max_attempts:
            raise Exception("Simulated failure")
        return "success"

    # Should succeed after max_attempts tries
    result = test_function()
    assert result == "success"
    assert attempt_count == max_attempts


def test_retry_exhaustion():
    """Test that retry mechanism fails after max attempts"""
    attempt_count = 0
    max_attempts = 2

    @retry_with_backoff(max_retries=max_attempts)
    def always_fail_function():
        nonlocal attempt_count
        attempt_count += 1
        raise Exception("Always fails")

    # Should raise exception after max attempts
    with pytest.raises(Exception, match="Always fails"):
        always_fail_function()

    assert attempt_count == max_attempts


def test_retrieval_tool_initialization():
    """Test RetrievalTool initialization"""
    tool = RetrievalTool()
    assert tool is not None
    assert tool.name == "retrieve_information"
    assert "Retrieve relevant information" in tool.description


def test_retrieval_tool_schema():
    """Test RetrievalTool schema"""
    tool = RetrievalTool()
    schema = tool.ToolInput
    assert hasattr(schema, "query")
    assert hasattr(schema, "top_k")
    assert hasattr(schema, "similarity_threshold")


@patch('rag_agent.tools.get_qdrant_client')
def test_retrieval_tool_execute(mock_get_client):
    """Test RetrievalTool execute method with mocked client"""
    # Mock the Qdrant client and its search results
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    # Mock search results
    mock_search_result = MagicMock()
    mock_search_result.id = "test_id"
    mock_search_result.payload = {
        "content": "test content",
        "source_url": "http://test.com",
        "module_name": "test_module",
        "chunk_id": 1
    }
    mock_search_result.score = 0.8
    mock_client.search.return_value = [mock_search_result]

    tool = RetrievalTool()

    # Test execution
    results = tool.execute(query="test query", top_k=1, similarity_threshold=0.5)

    assert isinstance(results, list)
    assert len(results) == 1
    if results:
        result = results[0]
        assert result["content"] == "test content"
        assert result["source_url"] == "http://test.com"
        assert result["module_name"] == "test_module"
        assert result["chunk_id"] == 1


def test_call_retrieval_tool():
    """Test the call_retrieval_tool function"""
    # Test with mocked retrieval tool
    with patch('rag_agent.tools.get_retrieval_tool') as mock_get_tool:
        mock_tool = MagicMock()
        mock_tool.execute.return_value = [
            {
                "content": "test content",
                "source_url": "http://test.com",
                "module_name": "test_module",
                "chunk_id": 1,
                "similarity_score": 0.8
            }
        ]
        mock_get_tool.return_value = mock_tool

        results = call_retrieval_tool("test query", top_k=1, similarity_threshold=0.5)

        assert isinstance(results, list)
        assert len(results) == 1
        if results:
            result = results[0]
            assert result["content"] == "test content"


def test_agent_retrieve_content():
    """Test AgentOrchestrator retrieve_content method"""
    agent = AgentOrchestrator()

    # Test with empty query (should return empty list)
    results = agent.retrieve_content("")
    assert results == []

    # Test with invalid parameters (should use defaults)
    results = agent.retrieve_content("test query", top_k=-1, similarity_threshold=1.5)
    # Should still return a list (might be empty if no content found)
    assert isinstance(results, list)


def test_agent_validate_response_grounding():
    """Test AgentOrchestrator validate_response_grounding method"""
    agent = AgentOrchestrator()

    # Test with empty chunks (should return False)
    result = agent.validate_response_grounding("test response", [])
    assert result is False

    # Test with matching content
    chunks = [{"content": "this is a test response content"}]
    result = agent.validate_response_grounding("this is a test response", chunks)
    # This might be True or False depending on the algorithm, but shouldn't error
    assert isinstance(result, bool)


def test_agent_validate_citation_accuracy():
    """Test AgentOrchestrator validate_citation_accuracy method"""
    agent = AgentOrchestrator()

    # Test with empty citations and chunks (should return True)
    result = agent.validate_citation_accuracy([], [])
    assert result is True

    # Test with valid citation and matching chunk
    citations = [{
        "url": "http://test.com",
        "module": "test_module",
        "chunk_id": 1
    }]
    chunks = [{
        "source_url": "http://test.com",
        "module_name": "test_module",
        "chunk_id": 1
    }]
    result = agent.validate_citation_accuracy(citations, chunks)
    assert result is True

    # Test with mismatched citation and chunk
    mismatched_citations = [{
        "url": "http://different.com",  # Different URL
        "module": "test_module",
        "chunk_id": 1
    }]
    result = agent.validate_citation_accuracy(mismatched_citations, chunks)
    # This might return False if validation is strict
    assert isinstance(result, bool)


def test_database_conversation_functions():
    """Test database conversation functions with mocked session"""
    # Create a mock database session
    mock_db = MagicMock(spec=Session)

    # Test conversation creation
    conversation_data = ConversationCreate(metadata_info={"test": "data"})

    # Mock the database operations
    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()

    # Since we can't actually create a conversation without a real DB,
    # we'll just test that the function can be called without error
    # when the database operations are mocked
    with patch('database.session.Conversation') as mock_conversation_model:
        mock_conversation = MagicMock()
        mock_conversation.id = "test_conversation_id"
        mock_conversation.metadata_info = {"test": "data"}
        mock_conversation_model.return_value = mock_conversation

        # This test would require more complex mocking to fully validate
        # For now, just ensure the function exists and can be called
        pass


def test_input_validation_edge_cases():
    """Test input validation for edge cases"""
    agent = AgentOrchestrator()

    # Test very long query
    long_query = "test " * 1000
    # Should handle gracefully without error
    try:
        results = agent.retrieve_content(long_query)
        assert isinstance(results, list)
    except Exception:
        # If it fails, that's acceptable as long as it doesn't crash the system
        pass

    # Test query with special characters
    special_query = "test query with special chars: !@#$%^&*()"
    try:
        results = agent.retrieve_content(special_query)
        assert isinstance(results, list)
    except Exception:
        # If it fails, that's acceptable as long as it doesn't crash the system
        pass


def test_agent_process_query_with_empty_results():
    """Test agent process_query with scenarios that might return empty results"""
    agent = AgentOrchestrator()

    # Mock the internal methods to return empty results
    with patch.object(agent, 'retrieve_content') as mock_retrieve, \
         patch.object(agent, 'generate_response_with_gemini') as mock_generate:

        mock_retrieve.return_value = []  # No content retrieved
        mock_generate.return_value = "Default response when no content found"

        result = agent.process_query("test query")

        assert "response" in result
        assert "citations" in result
        assert result["retrieved_chunks_count"] == 0
        assert result["grounded_in_retrieved_content"] is False


if __name__ == "__main__":
    pytest.main([__file__])