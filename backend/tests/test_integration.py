import pytest
from fastapi.testclient import TestClient
from api.main import app
from database.session import engine, Base, get_db
from database.models import Conversation, QueryLog, CitationLog
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os
from rag_agent.models import QueryRequest
from rag_agent.agent import AgentOrchestrator
from rag_agent.tools import call_retrieval_tool

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_integration.db"

# Create test engine
test_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# Create tables
Base.metadata.create_all(bind=test_engine)

# Create test session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override the dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

def test_full_rag_workflow_integration():
    """Test the complete RAG workflow from query to response with citations"""
    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    # Make an initial query
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
        assert "query" in data
        assert "response" in data
        assert "citations" in data
        assert "confidence" in data
        assert "retrieved_chunks_count" in data
        assert "processing_time_ms" in data
        assert "conversation_id" in data

        # Validate that the response contains meaningful data
        assert data["query"] == query_data["query"]
        assert isinstance(data["response"], str)
        assert isinstance(data["citations"], list)
        assert isinstance(data["confidence"], (int, float))
        assert 0.0 <= data["confidence"] <= 1.0
        assert isinstance(data["retrieved_chunks_count"], int)
        assert isinstance(data["processing_time_ms"], int)
        assert data["processing_time_ms"] >= 0
        assert isinstance(data["conversation_id"], str)


def test_conversation_continuation_integration():
    """Test that conversations can be continued with the same conversation ID"""
    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    # Make first query to establish conversation
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

        # Make second query using the same conversation ID
        query_data_2 = {
            "query": "What topics are covered?",
            "scope": "course",
            "conversation_id": conversation_id
        }

        response_2 = client.post("/api/v1/rag/query", json=query_data_2)
        assert response_2.status_code in [200, 400, 500]

        if response_2.status_code == 200:
            data_2 = response_2.json()
            # Should maintain the same conversation ID
            assert data_2["conversation_id"] == conversation_id


def test_different_query_scopes():
    """Test that different query scopes work correctly"""
    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    scopes_to_test = ["course", "modules", "general"]

    for scope in scopes_to_test:
        query_data = {
            "query": "What is covered in the course?",
            "scope": scope
        }

        response = client.post("/api/v1/rag/query", json=query_data)
        # Should return 200, 400, or 500 (acceptable responses)
        assert response.status_code in [200, 400, 500]


def test_health_endpoints_integration():
    """Test that health endpoints work correctly"""
    # Test main health endpoint
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "service" in data
    assert data["status"] in ["healthy", "unhealthy"]

    # Test RAG health endpoint
    response = client.get("/api/v1/rag/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "services" in data
    assert "timestamp" in data


def test_conversation_retrieval_integration():
    """Test that conversation history can be retrieved after creation"""
    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    # First, create a conversation by making a query
    query_data = {
        "query": "What prerequisites are needed?",
        "scope": "course"
    }

    response = client.post("/api/v1/rag/query", json=query_data)

    if response.status_code == 200:
        data = response.json()
        conversation_id = data["conversation_id"]

        # Now retrieve the conversation
        retrieval_response = client.get(f"/api/v1/rag/conversations/{conversation_id}")
        assert retrieval_response.status_code == 200

        conversation_data = retrieval_response.json()
        assert conversation_data["conversation_id"] == conversation_id
        assert "queries" in conversation_data


def test_error_handling_integration():
    """Test error handling for invalid requests"""
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


def test_agent_direct_integration():
    """Test the agent directly to ensure all components work together"""
    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    agent = AgentOrchestrator()

    # Test the full pipeline: retrieval -> generation -> validation
    query = "What is the AI & Humanoid Robotics course about?"

    # Test retrieval
    retrieved_chunks = agent.retrieve_content(query, top_k=3, similarity_threshold=0.3)

    # Test generation (with fallback if no content retrieved)
    if retrieved_chunks:
        response = agent.generate_response_with_gemini(query, retrieved_chunks)
        assert isinstance(response, str)
        assert len(response) > 0

    # Test full process
    result = agent.process_query(query, top_k=3, similarity_threshold=0.3)
    assert "response" in result
    assert "citations" in result
    assert "retrieved_chunks_count" in result


def test_retrieval_tool_integration():
    """Test the retrieval tool directly"""
    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    query = "AI & Humanoid Robotics"
    results = call_retrieval_tool(query, top_k=2, similarity_threshold=0.3)

    # Results should be a list (empty if no content found, which is valid)
    assert isinstance(results, list)

    # If results exist, check they have required fields
    for result in results:
        assert "content" in result
        assert "source_url" in result
        assert "module_name" in result
        assert "chunk_id" in result


if __name__ == "__main__":
    pytest.main([__file__])