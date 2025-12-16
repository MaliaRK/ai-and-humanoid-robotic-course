#!/usr/bin/env python3
"""
Ingestion script to load AI & Humanoid Robotics course documentation into Qdrant
This script will read all markdown files from the course documentation and create embeddings
"""

import os
import re
from pathlib import Path
import cohere
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv
import time
import logging
from typing import List, Dict
import uuid
import markdown
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

# Configuration constants
CHUNK_SIZE = 512  # Maximum size of each chunk in characters
CHUNK_OVERLAP = 50  # Overlap between chunks to maintain context
EMBEDDING_BATCH_SIZE = 5  # Reduced batch size for testing
MAX_RETRIES = 3  # Maximum number of retries for failed requests

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
            # Clear existing collection to start fresh
            qdrant_client.delete_collection(collection_name)
            qdrant_client.recreate_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE),
            )
            print(f"✅ Collection '{collection_name}' cleared and recreated.")

        return True  # Success

    except Exception as e:
        print(f"❌ Error creating collection '{collection_name}': {str(e)}")
        raise

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split text into overlapping chunks
    """
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # If we're near the end, just take the remainder
        if end > len(text):
            end = len(text)

        chunk = text[start:end]
        chunks.append(chunk)

        # Move start position by chunk_size minus overlap
        start = end - overlap

        # If start >= len(text), we're done
        if start >= len(text):
            break

    return chunks

def embed(cohere_client, text_chunks: List[str]) -> List[List[float]]:
    """
    Generate semantic embeddings for text chunks using Cohere
    """
    if not text_chunks:
        return []

    print(f"🧠 Generating embeddings for {len(text_chunks)} text chunks...")

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

def save_chunk_to_qdrant(qdrant_client, text_chunk: str, embedding: List[float], metadata: Dict, collection_name: str = "ai_book_embedding"):
    """
    Save a text chunk with its embedding and metadata to Qdrant
    """
    if not embedding or len(embedding) == 0:
        print(f"⚠️ Warning: Skipping chunk with empty embedding")
        return None

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
                "chunk_index": metadata.get("chunk_index", 0),
                "title": metadata.get("title", ""),
                "file_path": metadata.get("file_path", "")
            }
        )

        # Upsert the record into the collection
        qdrant_client.upsert(
            collection_name=collection_name,
            points=[record]
        )

        print(f"✅ Saved chunk to Qdrant: {metadata.get('title', 'Unknown')} - ID: {point_id[:8]}...")
        return point_id

    except Exception as e:
        print(f"❌ Error saving chunk to Qdrant: {str(e)}")
        raise

def extract_title_from_markdown(content: str) -> str:
    """
    Extract the first heading (title) from markdown content
    """
    lines = content.split('\n')
    for line in lines:
        if line.strip().startswith('# '):
            return line.strip()[2:]  # Remove '# ' prefix
        elif line.strip().startswith('## '):
            return line.strip()[3:]  # Remove '## ' prefix
    return "Untitled"

def read_markdown_files(docs_dir: str) -> List[Dict[str, str]]:
    """
    Recursively read all markdown files from the documentation directory
    """
    docs_dir = Path(docs_dir)
    markdown_files = []

    for md_file in docs_dir.rglob("*.md"):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract title from content
            title = extract_title_from_markdown(content)

            # Create a relative path for the source URL
            relative_path = md_file.relative_to(docs_dir.parent if docs_dir.parent.name == 'docs' else docs_dir)

            markdown_files.append({
                'content': content,
                'title': title,
                'file_path': str(relative_path),
                'source_url': f"https://ai-humanoid-robotics-course.com/docs/{relative_path}"
            })

            print(f"📄 Loaded: {title} from {relative_path}")

        except Exception as e:
            print(f"❌ Error reading {md_file}: {str(e)}")

    return markdown_files

def main():
    """Main function to ingest course documentation into Qdrant"""
    print("🚀 Starting Course Documentation Ingestion")
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

        # Read all markdown files from documentation
        print("\n📚 Reading course documentation files...")
        docs_path = "/home/maliaraees/ai-and-humanoid-robotics-course/docs"
        markdown_files = read_markdown_files(docs_path)

        if not markdown_files:
            print("❌ No markdown files found in the documentation directory")
            return

        print(f"✅ Loaded {len(markdown_files)} markdown files")

        # Process each file
        total_chunks = 0
        for i, file_data in enumerate(markdown_files):
            print(f"\n📝 Processing file {i+1}/{len(markdown_files)}: {file_data['title']}")

            # Convert markdown to plain text
            html = markdown.markdown(file_data['content'])
            soup = BeautifulSoup(html, 'html.parser')
            plain_text = soup.get_text()

            # Split content into chunks
            chunks = chunk_text(plain_text)
            print(f"✂️  Split into {len(chunks)} chunks")

            # Generate embeddings for chunks
            embeddings = embed(cohere_client, chunks)

            # Save each chunk with embedding to Qdrant
            print("💾 Saving chunks to Qdrant...")
            for j, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                if len(embedding) > 0:  # Only save if embedding is not empty
                    metadata = {
                        "source_url": file_data['source_url'],
                        "module_name": file_data['file_path'].split('/')[0] if '/' in file_data['file_path'] else 'general',
                        "chunk_index": j,
                        "title": file_data['title'],
                        "file_path": file_data['file_path']
                    }

                    point_id = save_chunk_to_qdrant(qdrant_client, chunk, embedding, metadata, "ai_book_embedding")
                    if point_id:
                        total_chunks += 1

        print(f"\n🎉 Success! Ingestion completed!")
        print(f"📊 Total chunks ingested: {total_chunks}")
        print(f"🔍 Check your Qdrant Cloud dashboard for the 'ai_book_embedding' collection.")

        # Verify the collection has content
        collection_info = qdrant_client.get_collection("ai_book_embedding")
        print(f"📈 Collection points count: {collection_info.points_count}")

    except Exception as e:
        print(f"❌ Error during ingestion: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\n Troubleshooting tips:")
        print("1. Verify your COHERE_API_KEY is correct and has sufficient credits")
        print("2. Verify your QDRANT_URL and QDRANT_API_KEY are correct")
        print("3. Check that both services are accessible from your network")
        print("4. Ensure you have installed all required packages: pip install -r requirements.txt")

if __name__ == "__main__":
    main()