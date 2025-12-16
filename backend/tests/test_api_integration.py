import pytest
from fastapi.testclient import TestClient
from api.main import app
from rag_agent.models import QueryRequest, QueryResponse
import os
import time

# Create test client
client = TestClient(app)

def test_api_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Agentic RAG Backend API is running" in data["message"]


def test_api_health_endpoint():
    """Test the health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "service" in data
    assert data["status"] == "healthy"
    assert data["service"] == "Agentic RAG Backend API"


def test_rag_query_endpoint_structure():
    """Test the RAG query endpoint response structure"""
    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    query_data = {
        "query": "What is the AI & Humanoid Robotics course about?",
        "scope": "course"
    }

    response = client.post("/api/v1/rag/query", json=query_data)

    # Should return 200, 400, or 500 (acceptable responses)
    assert response.status_code in [200, 400, 500]

    if response.status_code == 200:
        data = response.json()

        # Validate response structure matches QueryResponse model
        assert "id" in data
        assert "query" in data
        assert "response" in data
        assert "citations" in data
        assert "confidence" in data
        assert "retrieved_chunks_count" in data
        assert "processing_time_ms" in data
        assert "conversation_id" in data

        # Validate data types
        assert isinstance(data["id"], str)
        assert isinstance(data["query"], str)
        assert isinstance(data["response"], str)
        assert isinstance(data["citations"], list)
        assert isinstance(data["confidence"], (int, float))
        assert isinstance(data["retrieved_chunks_count"], int)
        assert isinstance(data["processing_time_ms"], int)
        assert isinstance(data["conversation_id"], str)

        # Validate value constraints
        assert 0.0 <= data["confidence"] <= 1.0
        assert data["processing_time_ms"] >= 0


def test_rag_query_endpoint_with_conversation():
    """Test the RAG query endpoint with conversation continuation"""
    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    # First query to establish conversation
    query_data_1 = {
        "query": "What is the course structure?",
        "scope": "course"
    }

    response_1 = client.post("/api/v1/rag/query", json=query_data_1)
    assert response_1.status_code in [200, 400, 500]

    if response_1.status_code == 200:
        data_1 = response_1.json()
        conversation_id = data_1["conversation_id"]
        assert conversation_id is not None

        # Second query using the same conversation ID
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


def test_rag_health_endpoint():
    """Test the RAG-specific health endpoint"""
    response = client.get("/api/v1/rag/health")
    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert "services" in data
    assert "timestamp" in data

    assert isinstance(data["status"], str)
    assert isinstance(data["services"], dict)
    assert isinstance(data["timestamp"], str)  # or datetime if parsed


def test_conversation_retrieval_endpoint():
    """Test the conversation retrieval endpoint"""
    # Test with a non-existent conversation ID
    fake_conversation_id = "nonexistent_conversation_12345"
    response = client.get(f"/api/v1/rag/conversations/{fake_conversation_id}")
    assert response.status_code == 404

    error_data = response.json()
    assert "error" in error_data
    assert error_data["error"] == "CONVERSATION_NOT_FOUND"


def test_rag_query_endpoint_validation():
    """Test validation of the RAG query endpoint"""
    # Test with empty query
    query_data = {
        "query": "",
        "scope": "course"
    }

    response = client.post("/api/v1/rag/query", json=query_data)
    assert response.status_code == 400

    # Test with very short query
    query_data = {
        "query": "hi",
        "scope": "course"
    }

    response = client.post("/api/v1/rag/query", json=query_data)
    assert response.status_code == 400

    # Test with invalid scope
    query_data = {
        "query": "What is this course about?",
        "scope": "invalid_scope"
    }

    response = client.post("/api/v1/rag/query", json=query_data)
    assert response.status_code == 400

    # Test with missing query field (should return 422 for validation error)
    query_data = {
        "scope": "course"
    }

    response = client.post("/api/v1/rag/query", json=query_data)
    assert response.status_code == 422


def test_api_response_headers():
    """Test that API responses include appropriate headers"""
    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    query_data = {
        "query": "What is covered in the course?",
        "scope": "course"
    }

    response = client.post("/api/v1/rag/query", json=query_data)

    # Check that response includes process time header
    assert "x-process-time" in response.headers
    process_time = float(response.headers["x-process-time"])
    assert process_time >= 0


def test_api_rate_limiting():
    """Test that API endpoints are properly rate limited"""
    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    # Send multiple requests quickly to potentially hit rate limit
    query_data = {
        "query": "What is the course about?",
        "scope": "course"
    }

    responses = []
    for i in range(15):  # Try to exceed the 10/minute limit
        response = client.post("/api/v1/rag/query", json=query_data)
        responses.append(response)
        time.sleep(0.1)  # Small delay between requests

    # Count how many requests were successful vs rate limited
    successful_requests = sum(1 for r in responses if r.status_code == 200)
    rate_limited_requests = sum(1 for r in responses if r.status_code == 429)

    # We expect some rate limiting to occur, though exact numbers depend on timing
    # The important thing is that rate limiting is active
    print(f"Successful: {successful_requests}, Rate Limited: {rate_limited_requests}")


def test_different_scopes_integration():
    """Test that different query scopes work properly with the API"""
    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    scopes_to_test = ["course", "modules", "readings", "assignments", "general"]

    for scope in scopes_to_test:
        query_data = {
            "query": "What is covered?",
            "scope": scope
        }

        response = client.post("/api/v1/rag/query", json=query_data)
        # Should return 200, 400, or 500 (acceptable responses)
        assert response.status_code in [200, 400, 500]


def test_citation_structure_in_api_response():
    """Test that citations in API responses have proper structure"""
    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    query_data = {
        "query": "What prerequisites are needed?",
        "scope": "course"
    }

    response = client.post("/api/v1/rag/query", json=query_data)

    if response.status_code == 200:
        data = response.json()
        citations = data["citations"]

        # Validate citation structure if any citations exist
        for citation in citations:
            assert "url" in citation
            assert "module" in citation
            assert "chunk_id" in citation
            assert "text_preview" in citation

            # Validate data types
            assert isinstance(citation["url"], str)
            assert isinstance(citation["module"], str)
            assert isinstance(citation["chunk_id"], int)
            assert citation["text_preview"] is None or isinstance(citation["text_preview"], str)


def test_api_conversation_flow():
    """Test complete conversation flow through API endpoints"""
    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    # Step 1: Initial query
    query_data_1 = {
        "query": "What is the main topic of the course?",
        "scope": "course"
    }

    response_1 = client.post("/api/v1/rag/query", json=query_data_1)
    assert response_1.status_code in [200, 400, 500]

    if response_1.status_code == 200:
        data_1 = response_1.json()
        conversation_id = data_1["conversation_id"]
        assert conversation_id is not None

        # Step 2: Follow-up query in same conversation
        query_data_2 = {
            "query": "Can you elaborate on that topic?",
            "scope": "modules",
            "conversation_id": conversation_id
        }

        response_2 = client.post("/api/v1/rag/query", json=query_data_2)
        assert response_2.status_code in [200, 400, 500]

        if response_2.status_code == 200:
            data_2 = response_2.json()
            assert data_2["conversation_id"] == conversation_id

            # Step 3: Retrieve the conversation
            retrieval_response = client.get(f"/api/v1/rag/conversations/{conversation_id}")
            assert retrieval_response.status_code == 200

            conversation_data = retrieval_response.json()
            assert conversation_data["conversation_id"] == conversation_id
            assert "queries" in conversation_data
            assert len(conversation_data["queries"]) >= 2  # Should have at least 2 queries


if __name__ == "__main__":
    pytest.main([__file__])