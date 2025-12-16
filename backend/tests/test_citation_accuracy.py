import pytest
from rag_agent.agent import AgentOrchestrator
from rag_agent.tools import call_retrieval_tool
import os

def test_citation_accuracy_basic():
    """Test basic citation accuracy functionality"""
    agent = AgentOrchestrator()

    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    # Test with a simple query
    query = "What is the AI & Humanoid Robotics course about?"

    # Retrieve content
    retrieved_chunks = call_retrieval_tool(query, top_k=3, similarity_threshold=0.3)

    # Validate retrieved chunks have required metadata
    if retrieved_chunks:
        for chunk in retrieved_chunks:
            assert "source_url" in chunk
            assert "module_name" in chunk
            assert "chunk_id" in chunk
            assert "content" in chunk
            assert isinstance(chunk["source_url"], str)
            assert isinstance(chunk["module_name"], str)
            assert isinstance(chunk["chunk_id"], int)
            assert isinstance(chunk["content"], str)

def test_citation_validation_function():
    """Test the citation validation function directly"""
    agent = AgentOrchestrator()

    # Create mock citation and chunk data
    mock_citation = {
        "url": "https://example.com/module1",
        "module": "Module 1",
        "chunk_id": 1,
        "text_preview": "This is a sample content preview"
    }

    mock_chunk = {
        "id": "test_id_123",
        "source_url": "https://example.com/module1",
        "module_name": "Module 1",
        "chunk_id": 1,
        "content": "This is a sample content preview for testing",
        "similarity_score": 0.8
    }

    # Test citation validation
    result = agent.validate_citation_accuracy([mock_citation], [mock_chunk])
    assert result == True, "Valid citation should pass validation"

def test_citation_validation_with_invalid_data():
    """Test citation validation with invalid data"""
    agent = AgentOrchestrator()

    # Create invalid citation (missing required field)
    invalid_citation = {
        "url": "https://example.com/module1",
        # Missing 'module' field
        "chunk_id": 1
    }

    mock_chunk = {
        "id": "test_id_123",
        "source_url": "https://example.com/module1",
        "module_name": "Module 1",
        "chunk_id": 1,
        "content": "This is a sample content",
        "similarity_score": 0.8
    }

    # Test citation validation with missing field
    result = agent.validate_citation_accuracy([invalid_citation], [mock_chunk])
    assert result == False, "Invalid citation should fail validation"

def test_citation_validation_with_mismatched_data():
    """Test citation validation with mismatched data"""
    agent = AgentOrchestrator()

    # Create citation with mismatched data
    citation = {
        "url": "https://example.com/module1",
        "module": "Module 1",
        "chunk_id": 1,
        "text_preview": "This is a sample content preview"
    }

    # Chunk with different values
    mismatched_chunk = {
        "id": "test_id_123",
        "source_url": "https://example.com/module2",  # Different URL
        "module_name": "Module 2",  # Different module
        "chunk_id": 2,  # Different chunk_id
        "content": "This is different content",
        "similarity_score": 0.8
    }

    # Test citation validation with mismatched data
    result = agent.validate_citation_accuracy([citation], [mismatched_chunk])
    assert result == False, "Mismatched citation should fail validation"

def test_citation_validation_empty_list():
    """Test citation validation with empty list"""
    agent = AgentOrchestrator()

    # Test with empty citations list
    result = agent.validate_citation_accuracy([], [])
    assert result == True, "Empty citations list should pass validation"

if __name__ == "__main__":
    pytest.main([__file__])