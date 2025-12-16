#!/usr/bin/env python3
"""
Test script to verify Qdrant connection and collection contents
"""

import os
from qdrant_client import QdrantClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="./.env")

# Initialize Qdrant client
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "ai_book_embedding")

print(f"Connecting to Qdrant at: {QDRANT_URL}")
print(f"Using collection: {QDRANT_COLLECTION_NAME}")

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)

try:
    # Get collection info
    collection_info = client.get_collection(QDRANT_COLLECTION_NAME)
    print(f"Collection '{QDRANT_COLLECTION_NAME}' exists!")
    print(f"Points count: {collection_info.points_count}")
    print(f"Collection config: {collection_info.config}")

    # Try to get a few points if they exist
    if collection_info.points_count > 0:
        points = client.scroll(
            collection_name=QDRANT_COLLECTION_NAME,
            limit=3,
            with_payload=True,
            with_vectors=False
        )

        print("\nSample points from collection:")
        for point in points[0]:  # points[0] contains the list of points
            print(f"ID: {point.id}")
            print(f"Payload keys: {list(point.payload.keys())}")
            if 'text' in point.payload:
                print(f"Text preview: {point.payload['text'][:100]}...")
            print("---")
    else:
        print("No points found in the collection.")

except Exception as e:
    print(f"Error accessing collection: {e}")

    # List all collections to see what's available
    try:
        collections = client.get_collections()
        print(f"\nAvailable collections: {[c.name for c in collections.collections]}")
    except Exception as list_e:
        print(f"Error listing collections: {list_e}")