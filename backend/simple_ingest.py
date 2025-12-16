#!/usr/bin/env python3
"""
Simple ingestion script to create Qdrant collection and verify the setup
This script will create the 'rag_embedding' collection in your Qdrant instance
"""

import os
import requests
from bs4 import BeautifulSoup
import cohere
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv
import time
import logging
from typing import List, Dict
import uuid
from urllib.parse import urljoin, urlparse

# Load environment variables
load_dotenv()

# Configuration constants
CHUNK_SIZE = 512  # Maximum size of each chunk in characters
CHUNK_OVERLAP = 50  # Overlap between chunks to maintain context
MAX_DEPTH = 2  # Maximum depth to crawl
REQUEST_TIMEOUT = 10  # Timeout for HTTP requests in seconds
MAX_RETRIES = 3  # Maximum number of retries for failed requests
EMBEDDING_BATCH_SIZE = 5  # Reduced batch size for testing

def initialize_cohere_client():
    """Initialize Cohere client with API key from environment variables"""
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        raise ValueError("COHERE_API_KEY environment variable is required")

    try:
        return cohere.Client(api_key)
    except Exception as e:
        raise ConnectionError(f"Failed to initialize Cohere client: {str(e)}")

def initialize_qdrant_client():
    """Initialize Qdrant client with connection details from environment variables"""
    url = os.getenv("QDRANT_URL")
    api_key = os.getenv("QDRANT_API_KEY")

    if not url or not api_key:
        raise ValueError("QDRANT_URL and QDRANT_API_KEY environment variables are required")

    try:
        return QdrantClient(url=url, api_key=api_key)
    except Exception as e:
        raise ConnectionError(f"Failed to initialize Qdrant client: {str(e)}")

def create_collection(qdrant_client, collection_name: str = "ai_book_embedding"):
    """
    Create a Qdrant collection for storing embeddings
    """
    try:
        # Check if collection already exists
        collections = qdrant_client.get_collections()
        collection_names = [collection.name for collection in collections.collections]

        if collection_name not in collection_names:
            # Create the collection with appropriate vector size for Cohere embeddings
            # Cohere's embed-english-v3.0 returns 1024-dimension vectors
            qdrant_client.recreate_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE),
            )
            print(f"✅ Collection '{collection_name}' created successfully with 1024-dimensional vectors.")
        else:
            print(f"ℹ️ Collection '{collection_name}' already exists.")

        return True  # Success

    except Exception as e:
        print(f"❌ Error creating collection '{collection_name}': {str(e)}")
        raise

def embed(cohere_client, text_chunks: List[str]) -> List[List[float]]:
    """
    Generate semantic embeddings for text chunks using Cohere
    """
    if not text_chunks:
        return []

    print(f".embedding {len(text_chunks)} text chunks...")

    # Process in batches to stay within API limits
    all_embeddings = []

    for i in range(0, len(text_chunks), EMBEDDING_BATCH_SIZE):
        batch = text_chunks[i:i + EMBEDDING_BATCH_SIZE]

        retry_count = 0
        while retry_count < MAX_RETRIES:
            try:
                response = cohere_client.embed(
                    texts=batch,
                    model="embed-english-v3.0",  # Using Cohere's latest embedding model
                    input_type="search_document"  # Optimize for search documents
                )

                # Extract embeddings from the response
                batch_embeddings = response.embeddings
                all_embeddings.extend(batch_embeddings)

                print(f"  Processed batch of {len(batch)} chunks, got {len(batch_embeddings)} embeddings")
                break  # Success, break out of retry loop

            except cohere.CohereAPIError as e:
                if "rate_limit" in str(e).lower() or e.status_code == 429:
                    print(f"  Rate limit hit, waiting before retry {retry_count + 1}/{MAX_RETRIES}")
                    time.sleep(2 ** retry_count)  # Exponential backoff
                    retry_count += 1
                    continue
                else:
                    print(f"  Cohere API error: {str(e)}")
                    # Don't retry for other API errors
                    break
            except Exception as e:
                print(f"  Error generating embeddings for batch: {str(e)}")
                retry_count += 1
                if retry_count >= MAX_RETRIES:
                    # If we've exhausted retries, add empty embeddings for this batch
                    all_embeddings.extend([[] for _ in range(len(batch))])
                else:
                    time.sleep(2 ** retry_count)  # Exponential backoff

    return all_embeddings

def save_chunk_to_qdrant(qdrant_client, text_chunk: str, embedding: List[float], metadata: Dict, collection_name: str = "rag_embedding"):
    """
    Save a text chunk with its embedding and metadata to Qdrant
    """
    if not embedding or len(embedding) == 0:
        raise ValueError("Embedding cannot be empty")

    # Verify embedding dimension matches expected size for the collection
    expected_dimension = 1024  # Standard for Cohere's embed-english-v3.0 model
    if len(embedding) != expected_dimension:
        print(f"⚠️ Warning: Embedding dimension mismatch. Expected {expected_dimension}, got {len(embedding)}")

    try:
        point_id = str(uuid.uuid4())

        # Prepare the record for Qdrant
        record = models.PointStruct(
            id=point_id,
            vector=embedding,
            payload={
                "text": text_chunk,
                "source_url": metadata.get("source_url", ""),
                "module_name": metadata.get("module_name", ""),
                "chunk_index": metadata.get("chunk_index", 0)
            }
        )

        # Upsert the record into the collection
        qdrant_client.upsert(
            collection_name=collection_name,
            points=[record]
        )

        print(f"✅ Successfully saved chunk to Qdrant with ID: {point_id}, vector dimension: {len(embedding)}")
        return point_id

    except Exception as e:
        print(f"❌ Error saving chunk to Qdrant: {str(e)}")
        raise

def main():
    """Main function to create collection and test the setup"""
    print("🚀 Starting Qdrant Collection Setup")
    print("=" * 50)

    try:
        # Initialize clients
        print("🔗 Initializing clients...")
        cohere_client = initialize_cohere_client()
        qdrant_client = initialize_qdrant_client()
        print("✅ Clients initialized successfully")

        # Create the collection
        print("\n📦 Creating Qdrant collection...")
        create_collection(qdrant_client, "ai_book_embedding")

        # Test with a simple embedding to verify the setup works
        print("\n📝 Testing with a sample text...")
        sample_texts = [
            "Artificial Intelligence and Machine Learning are transforming technology.",
            "Robotics combines mechanics, electronics, and computer science.",
            "Natural Language Processing enables computers to understand human language.",
            "Computer Vision allows machines to interpret and understand visual information.",
            "Reinforcement Learning uses rewards to train AI agents."
        ]

        print(f"🧠 Generating embeddings for {len(sample_texts)} sample texts...")
        embeddings = embed(cohere_client, sample_texts)

        if embeddings and len(embeddings) > 0:
            print(f"✅ Successfully generated {len(embeddings)} embeddings")

            # Save first embedding as a test
            print("\n💾 Saving test vectors to Qdrant...")
            for i, (text, embedding) in enumerate(zip(sample_texts, embeddings)):
                if len(embedding) > 0:  # Only save if embedding is not empty
                    metadata = {
                        "source_url": "https://test-url.com",
                        "module_name": f"test_module_{i}",
                        "chunk_index": i
                    }

                    point_id = save_chunk_to_qdrant(qdrant_client, text, embedding, metadata, "ai_book_embedding")
                    print(f"   Saved sample {i+1}/{len(sample_texts)}")

                    # Limit to first 3 samples to avoid using too many API calls
                    if i >= 2:
                        break

            print(f"\n🎉 Success! The 'ai_book_embedding' collection has been created and populated with test data.")
            print(f"📊 You should now see data in your Qdrant dashboard!")
            print(f"🔍 Check your Qdrant Cloud dashboard for the 'ai_book_embedding' collection.")
        else:
            print("❌ Failed to generate embeddings")

    except Exception as e:
        print(f"❌ Error during execution: {str(e)}")
        print("\n Troubleshooting tips:")
        print("1. Verify your COHERE_API_KEY is correct and has sufficient credits")
        print("2. Verify your QDRANT_URL and QDRANT_API_KEY are correct")
        print("3. Check that both services are accessible from your network")
        print("4. Ensure you have installed all required packages: pip install -r requirements.txt")

if __name__ == "__main__":
    main()