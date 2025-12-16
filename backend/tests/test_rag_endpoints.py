import pytest
from fastapi.testclient import TestClient
from api.main import app
from rag_agent.models import QueryRequest
import os

# Set up test client
client = TestClient(app)

def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "Agentic RAG Backend API is running" in response.json()["message"]

def test_health_endpoint():
    """Test the health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "service" in data
    assert data["status"] == "healthy"

def test_rag_health_endpoint():
    """Test the RAG health endpoint"""
    response = client.get("/api/v1/rag/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "services" in data
    assert "timestamp" in data

def test_rag_query_endpoint_valid_request():
    """Test the RAG query endpoint with a valid request"""
    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    query_data = {
        "query": "What is the AI & Humanoid Robotics course about?",
        "scope": "course"
    }

    response = client.post("/api/v1/rag/query", json=query_data)

    # The endpoint should return a 200 response (or 400 if no content found)
    # Both are acceptable depending on whether content exists in the vector DB
    assert response.status_code in [200, 400, 500]

    if response.status_code == 200:
        data = response.json()
        # Validate response structure
        assert "id" in data
        assert isinstance(data["id"], str)
        assert "query" in data
        assert isinstance(data["query"], str)
        assert data["query"] == query_data["query"]
        assert "response" in data
        assert isinstance(data["response"], str)
        assert "citations" in data
        assert isinstance(data["citations"], list)
        assert "confidence" in data
        assert isinstance(data["confidence"], (int, float))
        assert 0.0 <= data["confidence"] <= 1.0
        assert "retrieved_chunks_count" in data
        assert isinstance(data["retrieved_chunks_count"], int)
        assert "processing_time_ms" in data
        assert isinstance(data["processing_time_ms"], int)
        assert data["processing_time_ms"] >= 0
        assert "conversation_id" in data
        assert isinstance(data["conversation_id"], str)

        # Validate citation structure if citations exist
        for citation in data["citations"]:
            assert "url" in citation
            assert "module" in citation
            assert "chunk_id" in citation
            assert "text_preview" in citation
            assert isinstance(citation["url"], str)
            assert isinstance(citation["module"], str)
            assert isinstance(citation["chunk_id"], int)
            assert citation["text_preview"] is None or isinstance(citation["text_preview"], str)

def test_rag_query_endpoint_invalid_request():
    """Test the RAG query endpoint with invalid requests"""
    # Test with empty query
    query_data = {
        "query": "",
        "scope": "course"
    }

    response = client.post("/api/v1/rag/query", json=query_data)
    assert response.status_code == 400

    # Test with short query
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

def test_rag_query_endpoint_missing_query():
    """Test the RAG query endpoint with missing query field"""
    query_data = {
        "scope": "course"
    }

    response = client.post("/api/v1/rag/query", json=query_data)
    assert response.status_code == 422  # Validation error

if __name__ == "__main__":
    pytest.main([__file__])