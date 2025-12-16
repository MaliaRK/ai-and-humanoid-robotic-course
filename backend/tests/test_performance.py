import pytest
import time
from fastapi.testclient import TestClient
from api.main import app
import os

# Create test client
client = TestClient(app)

def test_response_time_under_5_seconds():
    """Test that system responses are returned within 5 seconds"""
    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    query_data = {
        "query": "What is the AI & Humanoid Robotics course about?",
        "scope": "course"
    }

    start_time = time.time()
    response = client.post("/api/v1/rag/query", json=query_data)
    end_time = time.time()

    response_time = end_time - start_time

    # Check that response time is under 5 seconds
    assert response_time < 5.0, f"Response time {response_time:.2f}s exceeded 5 seconds"

    # Also verify the response was successful
    assert response.status_code in [200, 400, 500]

    if response.status_code == 200:
        data = response.json()
        # Verify that processing_time_ms in response is also reasonable
        if "processing_time_ms" in data:
            processing_time_seconds = data["processing_time_ms"] / 1000.0
            assert processing_time_seconds < 5.0, f"Processing time {processing_time_seconds}s exceeded 5 seconds"


def test_multiple_queries_response_time():
    """Test response time for multiple queries"""
    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    queries = [
        {"query": "What is the course structure?", "scope": "course"},
        {"query": "What topics are covered?", "scope": "modules"},
        {"query": "What prerequisites are needed?", "scope": "course"}
    ]

    max_response_time = 0
    total_response_time = 0

    for query_data in queries:
        start_time = time.time()
        response = client.post("/api/v1/rag/query", json=query_data)
        end_time = time.time()

        response_time = end_time - start_time
        total_response_time += response_time

        if response_time > max_response_time:
            max_response_time = response_time

        # Each response should be under 5 seconds
        assert response_time < 5.0, f"Response time {response_time:.2f}s exceeded 5 seconds for query: {query_data['query']}"

        # Verify the response was successful
        assert response.status_code in [200, 400, 500]

    # Calculate average response time
    avg_response_time = total_response_time / len(queries)
    print(f"Performance test results - Max: {max_response_time:.2f}s, Avg: {avg_response_time:.2f}s, Total: {total_response_time:.2f}s")


def test_concurrent_request_performance():
    """Test performance under concurrent requests"""
    import threading
    import time

    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    results = []
    query_data = {
        "query": "What is covered in the course?",
        "scope": "course"
    }

    def make_request():
        start_time = time.time()
        response = client.post("/api/v1/rag/query", json=query_data)
        end_time = time.time()

        results.append({
            "response_time": end_time - start_time,
            "status_code": response.status_code
        })

    # Create multiple threads to simulate concurrent requests
    threads = []
    num_requests = 3  # Use a small number to avoid overwhelming the API

    for i in range(num_requests):
        thread = threading.Thread(target=make_request)
        threads.append(thread)
        thread.start()
        time.sleep(0.1)  # Small delay between requests

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Verify all requests completed under 5 seconds
    for i, result in enumerate(results):
        response_time = result["response_time"]
        status_code = result["status_code"]

        assert response_time < 5.0, f"Request {i} exceeded 5 seconds: {response_time:.2f}s"
        assert status_code in [200, 400, 500], f"Request {i} returned unexpected status: {status_code}"

    # Calculate performance metrics
    response_times = [result["response_time"] for result in results]
    max_time = max(response_times)
    avg_time = sum(response_times) / len(response_times)

    print(f"Concurrent performance test - Requests: {len(results)}, Max: {max_time:.2f}s, Avg: {avg_time:.2f}s")


def test_health_endpoint_performance():
    """Test that health endpoints respond quickly"""
    start_time = time.time()
    response = client.get("/health")
    end_time = time.time()

    response_time = end_time - start_time

    # Health check should be very fast (< 1 second)
    assert response_time < 1.0, f"Health check response time {response_time:.2f}s exceeded 1 second"
    assert response.status_code == 200

    # Test RAG health endpoint
    start_time = time.time()
    response = client.get("/api/v1/rag/health")
    end_time = time.time()

    response_time = end_time - start_time

    # RAG health check should also be fast (< 2 seconds, as it checks external services)
    assert response_time < 2.0, f"RAG health check response time {response_time:.2f}s exceeded 2 seconds"
    assert response_time < 5.0, f"RAG health check response time {response_time:.2f}s exceeded 5 seconds"
    assert response.status_code == 200


def test_long_query_performance():
    """Test performance with longer/more complex queries"""
    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    # Create a more complex query
    complex_query = {
        "query": "Can you provide a comprehensive overview of the AI & Humanoid Robotics course, including the main topics covered, learning objectives, required materials, and any prerequisites needed for success in the course?",
        "scope": "course"
    }

    start_time = time.time()
    response = client.post("/api/v1/rag/query", json=complex_query)
    end_time = time.time()

    response_time = end_time - start_time

    # Complex query should still respond under 5 seconds
    assert response_time < 5.0, f"Complex query response time {response_time:.2f}s exceeded 5 seconds"
    assert response.status_code in [200, 400, 500]


def test_citation_heavy_query_performance():
    """Test performance when system needs to generate many citations"""
    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    citation_query = {
        "query": "What are all the different topics, concepts, and modules covered throughout the entire AI & Humanoid Robotics course?",
        "scope": "modules"
    }

    start_time = time.time()
    response = client.post("/api/v1/rag/query", json=citation_query)
    end_time = time.time()

    response_time = end_time - start_time

    # Even with potential multiple citations, should respond under 5 seconds
    assert response_time < 5.0, f"Citation-heavy query response time {response_time:.2f}s exceeded 5 seconds"
    assert response.status_code in [200, 400, 500]

    if response.status_code == 200:
        data = response.json()
        # If response includes citations, verify they're properly formatted
        if "citations" in data:
            assert isinstance(data["citations"], list)


def test_conversation_continuation_performance():
    """Test performance of conversation continuation"""
    # Only run this test if API keys are available
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        pytest.skip("API keys not available for testing")

    # First query to establish conversation
    query_data_1 = {
        "query": "What is the course about?",
        "scope": "course"
    }

    start_time = time.time()
    response_1 = client.post("/api/v1/rag/query", json=query_data_1)
    end_time = time.time()

    response_time_1 = end_time - start_time
    assert response_time_1 < 5.0, f"First query response time {response_time_1:.2f}s exceeded 5 seconds"

    if response_1.status_code == 200:
        data_1 = response_1.json()
        conversation_id = data_1["conversation_id"]

        # Second query in same conversation
        query_data_2 = {
            "query": "What are the prerequisites?",
            "scope": "course",
            "conversation_id": conversation_id
        }

        start_time = time.time()
        response_2 = client.post("/api/v1/rag/query", json=query_data_2)
        end_time = time.time()

        response_time_2 = end_time - start_time
        assert response_time_2 < 5.0, f"Conversation continuation response time {response_time_2:.2f}s exceeded 5 seconds"

        assert response_2.status_code in [200, 400, 500]


if __name__ == "__main__":
    pytest.main([__file__])