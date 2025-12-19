#!/usr/bin/env python3
"""
Quick test script to verify Qdrant retrieval functionality
"""
import os
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from retrieval.search import search_similar_chunks
from rag_agent.config import QDRANT_COLLECTION_NAME

def test_retrieval():
    """Test retrieval functionality"""
    try:
        # Initialize Qdrant client
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")

        if qdrant_api_key:
            qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        else:
            qdrant_client = QdrantClient(url=qdrant_url)

        print(f"Connected to Qdrant at {qdrant_url}")

        # Check collection info
        collection_info = qdrant_client.get_collection(QDRANT_COLLECTION_NAME)
        print(f"Collection '{QDRANT_COLLECTION_NAME}' exists with {collection_info.points_count} points")

        # Test search with a sample query
        test_queries = [
            "What is ROS2?",
            "Explain digital twin in robotics",
            "How does VLA work?",
            "humanoid robotics"
        ]

        for query in test_queries:
            print(f"\nTesting query: '{query}'")
            results = search_similar_chunks(qdrant_client, query)
            print(f"Found {len(results)} results")

            if results:
                for i, result in enumerate(results[:2]):  # Show first 2 results
                    print(f"  Result {i+1}:")
                    print(f"    Score: {result['similarity_score']:.3f}")
                    # Clean content to handle encoding issues
                    clean_content = result['content'][:200].encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
                    print(f"    Content: {clean_content}...")
                    print(f"    Source: {result['source_url']}")
            else:
                print("  No results found")

    except Exception as e:
        print(f"Error during retrieval test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_retrieval()