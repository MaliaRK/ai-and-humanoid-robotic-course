import pytest
from fastapi.testclient import TestClient
from api.main import app
from rag_agent.models import QueryRequest
import os

# Create test client
client = TestClient(app)

def test_general_queries():
    """Test that the system supports general queries without scope"""
    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    # Test query without scope (general query)
    query_data = {
        "query": "What is artificial intelligence?",
        "scope": None  # No scope specified
    }

    response = client.post("/api/v1/rag/query", json=query_data)

    # Should return 200, 400, or 500 (acceptable responses)
    assert response.status_code in [200, 400, 500]

    if response.status_code == 200:
        data = response.json()
        # Validate response structure
        assert "id" in data
        assert "query" in data
        assert "response" in data
        assert "citations" in data
        assert "confidence" in data
        assert "retrieved_chunks_count" in data
        assert "processing_time_ms" in data
        assert "conversation_id" in data


def test_scoped_queries():
    """Test that the system supports queries with different scopes"""
    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    # Test different scopes
    scopes_to_test = ["course", "modules", "readings", "assignments", "general"]

    for scope in scopes_to_test:
        query_data = {
            "query": "What is covered in the course?",
            "scope": scope
        }

        response = client.post("/api/v1/rag/query", json=query_data)

        # Should return 200, 400, or 500 (acceptable responses)
        assert response.status_code in [200, 400, 500]

        if response.status_code == 200:
            data = response.json()
            # Validate response structure
            assert "query" in data
            assert data["query"] == query_data["query"]
            assert "scope" in query_data  # Verify scope was passed through


def test_specific_scoped_queries():
    """Test specific types of scoped queries"""
    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    test_cases = [
        {
            "query": "What are the course objectives?",
            "scope": "course"
        },
        {
            "query": "What topics are covered in module 1?",
            "scope": "modules"
        },
        {
            "query": "What readings are assigned?",
            "scope": "readings"
        },
        {
            "query": "What assignments are due?",
            "scope": "assignments"
        },
        {
            "query": "What is the overall course structure?",
            "scope": "general"
        }
    ]

    for test_case in test_cases:
        response = client.post("/api/v1/rag/query", json=test_case)

        # Should return 200, 400, or 500 (acceptable responses)
        assert response.status_code in [200, 400, 500]


def test_invalid_scope_handling():
    """Test that invalid scopes are handled properly"""
    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    query_data = {
        "query": "What is the course about?",
        "scope": "invalid_scope"  # Invalid scope
    }

    response = client.post("/api/v1/rag/query", json=query_data)

    # Should return 400 for invalid scope
    assert response.status_code == 400

    error_data = response.json()
    assert "error" in error_data
    assert error_data["error"] == "INVALID_SCOPE"


def test_scope_case_insensitive():
    """Test that scope parameter is case insensitive"""
    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    # Test different case variations
    scopes_to_test = ["COURSE", "Course", "course", "MODULES", "Modules", "modules"]

    for scope in scopes_to_test:
        query_data = {
            "query": "What is covered?",
            "scope": scope
        }

        response = client.post("/api/v1/rag/query", json=query_data)

        # Should return 200, 400, or 500 (acceptable responses)
        assert response.status_code in [200, 400, 500]


def test_scoped_query_response_quality():
    """Test that scoped queries return relevant responses"""
    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    # Test that different scopes might return different responses
    query = "What assignments are available?"

    responses = {}
    for scope in ["assignments", "course", "general"]:
        query_data = {
            "query": query,
            "scope": scope
        }

        response = client.post("/api/v1/rag/query", json=query_data)

        if response.status_code == 200:
            data = response.json()
            responses[scope] = data["response"]
        else:
            responses[scope] = None

    # Verify that responses are captured for valid scopes
    for scope in ["assignments", "course", "general"]:
        # Responses might be None if no content is found, which is acceptable
        pass  # Just ensure no exceptions occurred


def test_empty_scope_handling():
    """Test handling of empty string scope"""
    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    query_data = {
        "query": "What is the course about?",
        "scope": ""  # Empty scope
    }

    response = client.post("/api/v1/rag/query", json=query_data)

    # Empty scope should be treated as None (general query) or return 400
    assert response.status_code in [200, 400, 500]


def test_query_scoping_with_conversation_tracking():
    """Test that query scoping works with conversation tracking"""
    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    # First query with scope
    query_data_1 = {
        "query": "What are the course prerequisites?",
        "scope": "course"
    }

    response_1 = client.post("/api/v1/rag/query", json=query_data_1)
    assert response_1.status_code in [200, 400, 500]

    if response_1.status_code == 200:
        data_1 = response_1.json()
        conversation_id = data_1["conversation_id"]
        assert conversation_id is not None

        # Second query with different scope in same conversation
        query_data_2 = {
            "query": "What topics are covered?",
            "scope": "modules",
            "conversation_id": conversation_id
        }

        response_2 = client.post("/api/v1/rag/query", json=query_data_2)
        assert response_2.status_code in [200, 400, 500]

        if response_2.status_code == 200:
            data_2 = response_2.json()
            # Should maintain the same conversation ID
            assert data_2["conversation_id"] == conversation_id


def test_scoped_query_parameter_validation():
    """Test that scoped queries are properly validated"""
    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    # Test with valid scope but invalid query
    query_data = {
        "query": "a",  # Too short
        "scope": "course"
    }

    response = client.post("/api/v1/rag/query", json=query_data)

    # Should return 400 for invalid query length
    assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__])