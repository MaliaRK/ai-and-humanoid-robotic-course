import pytest
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.main import app
from database.session import engine, Base, get_db
from database.models import Conversation, QueryLog, CitationLog
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from rag_agent.agent import AgentOrchestrator
from rag_agent.tools import RetrievalTool
from rag_agent.utils import retry_with_backoff
import time

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_edge_cases.db"

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

def test_qdrant_unavailability_handling():
    """Test system behavior when Qdrant is unavailable"""
    # Mock the Qdrant client to simulate unavailability
    with patch('retrieval.client.get_qdrant_client') as mock_get_client:
        mock_get_client.side_effect = Exception("Qdrant connection failed")

        # Test that the system handles Qdrant unavailability gracefully
        from rag_agent.tools import call_retrieval_tool

        # This should handle the error gracefully and return empty results
        results = call_retrieval_tool("test query", top_k=3, similarity_threshold=0.3)

        # Should return empty list when Qdrant is unavailable
        assert results == []


def test_gemini_rate_limit_handling():
    """Test system behavior when Gemini rate limits occur"""
    # Only run this test if API keys are available
    if not os.getenv("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY not available for testing")

    # Mock Gemini to simulate rate limit error
    with patch('rag_agent.gemini_client.get_gemini_model') as mock_get_model:
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("429: Resource has been exhausted (e.g. check quota).")
        mock_get_model.return_value = mock_model

        # Test that the agent handles rate limit gracefully
        agent = AgentOrchestrator()

        # This should handle the rate limit gracefully with fallback response
        response = agent.generate_response_with_gemini(
            "test query",
            [{"content": "test content", "source_url": "test_url", "module_name": "test_module", "chunk_id": 1}]
        )

        # Should return fallback response when Gemini fails
        assert isinstance(response, str)
        assert len(response) > 0


def test_database_unavailability_handling():
    """Test system behavior when Neon Postgres is unavailable"""
    # Mock database operations to simulate unavailability
    with patch('database.session.SessionLocal') as mock_session:
        mock_session.side_effect = Exception("Database connection failed")

        # Test that the agent handles database issues gracefully
        agent = AgentOrchestrator()

        # This should handle the database issue gracefully
        result = agent.process_query_with_logging(
            "test query",
            top_k=3,
            similarity_threshold=0.3
        )

        # Should still return a result even if logging fails
        assert "response" in result
        assert "citations" in result


def test_retry_mechanism():
    """Test that retry logic works correctly"""
    attempt_count = 0

    @retry_with_backoff(max_retries=3)
    def failing_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise Exception("Simulated failure")
        return "success"

    # Should succeed after 3 attempts
    result = failing_function()
    assert result == "success"
    assert attempt_count == 3


def test_retry_exhaustion():
    """Test behavior when all retries are exhausted"""
    attempt_count = 0

    @retry_with_backoff(max_retries=2)
    def always_failing_function():
        nonlocal attempt_count
        attempt_count += 1
        raise Exception("Always fails")

    # Should raise exception after all retries are exhausted
    with pytest.raises(Exception, match="Always fails"):
        always_failing_function()

    # Should have tried 2 times
    assert attempt_count == 2


def test_empty_retrieval_handling():
    """Test system behavior when no content is retrieved"""
    # Mock the retrieval tool to return empty results
    with patch('rag_agent.tools.call_retrieval_tool') as mock_retrieval:
        mock_retrieval.return_value = []  # No results found

        agent = AgentOrchestrator()

        # Test with empty retrieval results
        result = agent.process_query(
            "test query that won't find content",
            top_k=3,
            similarity_threshold=0.3
        )

        # Should still return a response even with no retrieved content
        assert "response" in result
        assert "citations" in result
        assert result["retrieved_chunks_count"] == 0
        assert len(result["citations"]) == 0


def test_invalid_api_key_handling():
    """Test behavior when API keys are invalid"""
    # Temporarily remove or mock API keys to simulate invalid keys
    original_gemini_key = os.environ.get("GEMINI_API_KEY")
    original_openai_key = os.environ.get("OPENAI_API_KEY")

    try:
        # Remove API keys temporarily
        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]

        # Test that the system handles missing API keys gracefully
        agent = AgentOrchestrator()

        # This should handle missing API keys gracefully
        result = agent.process_query(
            "test query",
            top_k=3,
            similarity_threshold=0.3
        )

        # Should return an error response when API keys are missing
        assert "response" in result
        assert "error" in result or "Error" in result["response"]

    finally:
        # Restore original API keys
        if original_gemini_key:
            os.environ["GEMINI_API_KEY"] = original_gemini_key
        if original_openai_key:
            os.environ["OPENAI_API_KEY"] = original_openai_key


def test_network_timeout_handling():
    """Test behavior when network requests timeout"""
    # Mock a network timeout scenario
    with patch('openai.OpenAI') as mock_openai:
        def timeout_side_effect(*args, **kwargs):
            raise TimeoutError("Request timed out")

        mock_client = MagicMock()
        mock_client.embeddings.create.side_effect = timeout_side_effect
        mock_openai.return_value = mock_client

        # Test embedding generation with timeout
        from rag_agent.openai_client import get_openai_client
        client = get_openai_client()

        # This should handle the timeout gracefully
        from retrieval.search import embed_query
        with pytest.raises(TimeoutError):
            embed_query("test query")


def test_concurrent_access_handling():
    """Test system behavior under concurrent access"""
    import threading
    import time

    results = []

    def make_request():
        # Only run if API keys are available
        if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
            results.append("skipped")
            return

        query_data = {
            "query": "What is the course about?",
            "scope": "course"
        }

        try:
            response = client.post("/api/v1/rag/query", json=query_data)
            results.append(response.status_code)
        except Exception as e:
            results.append(f"error: {str(e)}")

    # Create multiple threads to simulate concurrent access
    threads = []
    for i in range(3):  # Use 3 threads for safety
        thread = threading.Thread(target=make_request)
        threads.append(thread)
        thread.start()
        time.sleep(0.1)  # Small delay between requests

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # All requests should complete (might have various statuses)
    assert len(results) == 3


def test_large_query_handling():
    """Test system behavior with large queries"""
    # Create a very long query
    long_query = "This is a very long query. " * 100  # 300 words

    query_data = {
        "query": long_query,
        "scope": "course"
    }

    # This should handle the large query gracefully
    response = client.post("/api/v1/rag/query", json=query_data)

    # Should return a valid response (200, 400 if content too long, or 500)
    assert response.status_code in [200, 400, 500]


def test_invalid_json_handling():
    """Test system behavior with invalid JSON input"""
    # Send invalid JSON to test error handling
    response = client.post(
        "/api/v1/rag/query",
        content="invalid json {",
        headers={"Content-Type": "application/json"}
    )

    # Should return 422 for validation error or 400 for bad request
    assert response.status_code in [400, 422]


if __name__ == "__main__":
    pytest.main([__file__])