#!/usr/bin/env python3
"""
Test script to verify retrieval function works correctly
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="./.env")

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_retrieval():
    """Test the retrieval function directly"""
    print("Testing retrieval function...")

    try:
        # Import the retrieval components
        from retrieval.client import get_qdrant_client
        from rag_agent.config import QDRANT_COLLECTION_NAME
        from retrieval.search import search_similar_chunks

        print(f"Using collection: {QDRANT_COLLECTION_NAME}")

        # Get Qdrant client
        qdrant_client = get_qdrant_client()
        print("Qdrant client connected successfully")

        # Test search
        query = "What is Artificial Intelligence?"
        print(f"Searching for: '{query}'")

        results = search_similar_chunks(
            qdrant_client=qdrant_client,
            query=query,
            collection_name=QDRANT_COLLECTION_NAME,
            top_k=3,
            similarity_threshold=0.1
        )

        print(f"Found {len(results)} results:")
        for i, result in enumerate(results):
            print(f"Result {i+1}:")
            print(f"  Text: {result.get('content', '')[:100]}...")
            print(f"  Source: {result.get('source_url', 'N/A')}")
            print(f"  Score: {result.get('similarity_score', 0.0)}")
            print()

        return True

    except Exception as e:
        print(f"Error in retrieval test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agent_query():
    """Test the agent query function"""
    print("\nTesting agent query function...")

    try:
        from rag_agent.agent import run_agent_query

        query = "What is AI?"
        print(f"Running agent query: '{query}'")

        # This will take some time due to the full pipeline
        result = run_agent_query(
            query=query,
            top_k=3,
            similarity_threshold=0.1,
            conversation_id=None
        )

        print(f"Agent result: {result}")
        return True

    except Exception as e:
        print(f"Error in agent query test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting retrieval tests...\n")

    success1 = test_retrieval()
    print(f"Retrieval test: {'PASSED' if success1 else 'FAILED'}\n")

    success2 = test_agent_query()
    print(f"Agent query test: {'PASSED' if success2 else 'FAILED'}\n")

    print("Tests completed.")