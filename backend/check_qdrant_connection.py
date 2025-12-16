#!/usr/bin/env python3
"""
Simple script to check Qdrant connection and list collections
Run this script to verify your Qdrant Cloud connection and see existing collections
"""

import os
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_qdrant_connection():
    """Check Qdrant connection and list collections"""
    try:
        # Get credentials from environment
        url = os.getenv("QDRANT_URL")
        api_key = os.getenv("QDRANT_API_KEY")

        if not url or not api_key:
            print("❌ Error: QDRANT_URL and QDRANT_API_KEY environment variables are required")
            print("Please set them in your .env file:")
            print("QDRANT_URL=your_qdrant_cloud_url")
            print("QDRANT_API_KEY=your_qdrant_api_key")
            return

        print(f"📍 Connecting to Qdrant at: {url}")

        # Initialize Qdrant client
        client = QdrantClient(url=url, api_key=api_key)

        # Test connection by listing collections
        print("\n🔍 Checking collections in your Qdrant instance...")
        collections = client.get_collections()

        print(f"\n📊 Found {len(collections.collections)} collection(s):")
        for collection in collections.collections:
            # Get collection info
            info = client.get_collection(collection.name)
            print(f"  • {collection.name}")
            print(f"    Points: {info.points_count}")
            print(f"    Vector size: {info.config.params.vectors.size}")
            print(f"    Distance: {info.config.params.vectors.distance}")

        if len(collections.collections) == 0:
            print("  No collections found in your Qdrant instance")

        print(f"\n✅ Successfully connected to Qdrant!")
        print(f"Your collections should be visible in your Qdrant Cloud dashboard at: {url.replace('https://', '').split(':')[0] if ':' in url else url.replace('https://', '')}")

        # Check for the specific collection we use in the main script
        target_collection = "rag_embedding"
        collection_exists = any(col.name == target_collection for col in collections.collections)

        if collection_exists:
            print(f"\n🎯 Found '{target_collection}' collection - data should be visible in your dashboard!")
        else:
            print(f"\n💡 The '{target_collection}' collection does not exist yet. Run the main ingestion script to create it and populate it with data.")

        return True

    except Exception as e:
        print(f"❌ Error connecting to Qdrant: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Verify your QDRANT_URL and QDRANT_API_KEY are correct")
        print("2. Ensure your Qdrant Cloud instance is accessible")
        print("3. Check that your firewall allows outbound connections")
        print("4. Verify your API key has the necessary permissions")
        return False

if __name__ == "__main__":
    print("🔍 Qdrant Connection Checker")
    print("=" * 40)
    check_qdrant_connection()