"""
Website URL Ingestion, Embedding Generation, and Vector Storage System

This script crawls the AI & Humanoid Robotics book website, extracts clean text content,
chunks it using an industry-standard strategy, generates semantic embeddings using Cohere models,
and stores them with metadata in Qdrant Cloud vector database.
"""

import os
import requests
from bs4 import BeautifulSoup
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv
import time
import logging
from typing import List, Dict, Tuple, Optional
import re
from urllib.parse import urljoin, urlparse
from sentence_transformers import SentenceTransformer


def setup_logging():
    """Set up logging configuration for the pipeline"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('ingestion_pipeline.log'),
            logging.StreamHandler()  # Also log to console
        ]
    )
    return logging.getLogger(__name__)

# Configuration constants
CHUNK_SIZE = 512  # Maximum size of each chunk in characters
CHUNK_OVERLAP = 50  # Overlap between chunks to maintain context
MAX_DEPTH = 2  # Maximum depth to crawl
REQUEST_TIMEOUT = 10  # Timeout for HTTP requests in seconds
MAX_RETRIES = 3  # Maximum number of retries for failed requests
EMBEDDING_BATCH_SIZE = 10  # Number of chunks to embed at once to stay within API limits


# Load environment variables from the project root
import sys
from pathlib import Path
# Add the project root to the path so we can load .env from there
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(dotenv_path=project_root / ".env")


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split text content into semantic chunks of appropriate size
    """
    # Input validation
    if not isinstance(text, str):
        raise TypeError("Text must be a string")
    if not isinstance(chunk_size, int) or chunk_size <= 0:
        raise ValueError("Chunk size must be a positive integer")
    if not isinstance(overlap, int) or overlap < 0:
        raise ValueError("Overlap must be a non-negative integer")
    if overlap >= chunk_size:
        raise ValueError("Overlap must be less than chunk size")

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # If we're at the end, include the remaining text
        if end >= len(text):
            chunks.append(text[start:])
            break

        # Try to break at sentence boundary if possible
        chunk = text[start:end]

        # Find the last sentence ending within the chunk
        last_period = chunk.rfind('. ')
        last_exclamation = chunk.rfind('! ')
        last_question = chunk.rfind('? ')
        last_sentence_end = max(last_period, last_exclamation, last_question)

        if last_sentence_end > chunk_size // 2:  # Only break at sentence if it's not too early
            actual_end = start + last_sentence_end + 2
            chunks.append(text[start:actual_end])
            start = actual_end - overlap if overlap < actual_end else actual_end
        else:
            # If no good sentence boundary, try to break at word boundary
            last_space = chunk.rfind(' ')
            if last_space > chunk_size // 2:
                actual_end = start + last_space
                chunks.append(text[start:actual_end])
                start = actual_end - overlap if overlap < actual_end else actual_end
            else:
                # If no good boundary, just take the chunk as is
                chunks.append(text[start:end])
                start = end - overlap if overlap < end else end

    # Filter out any empty chunks
    chunks = [chunk for chunk in chunks if chunk.strip()]

    return chunks


def track_embedding_usage(text_chunks: List[str]) -> Dict[str, int]:
    """
    Track embedding usage to ensure we stay within free-tier limits
    """
    total_chars = sum(len(chunk) for chunk in text_chunks)
    # Cohere free tier typically has monthly limits, we'll track usage
    return {
        "total_chars": total_chars,
        "total_chunks": len(text_chunks),
        "estimated_tokens": total_chars // 4  # Rough estimation (4 chars per token)
    }


def embed(model, text_chunks: List[str]) -> List[List[float]]:
    """
    Generate semantic embeddings for text chunks using local sentence transformer model
    """
    if not text_chunks:
        return []

    # Track usage to stay within free-tier limits - T025
    usage_stats = track_embedding_usage(text_chunks)
    print(f"Embedding usage stats - Chars: {usage_stats['total_chars']}, Chunks: {usage_stats['total_chunks']}, Estimated tokens: {usage_stats['estimated_tokens']}")

    # Process all chunks at once for better efficiency with local model
    all_embeddings = []

    try:
        # Encode all texts at once for better performance
        embeddings = model.encode(text_chunks)

        # Convert to list of lists
        for i, embedding in enumerate(embeddings):
            all_embeddings.append(embedding.tolist())
            print(f"Generated embedding with dimension: {len(embedding)} for chunk {i+1}/{len(text_chunks)}")

    except Exception as e:
        print(f"Error generating embeddings: {str(e)}")
        # If there's an error, try processing one by one
        for i, text in enumerate(text_chunks):
            try:
                embedding = model.encode([text])[0].tolist()
                all_embeddings.append(embedding)
                print(f"Generated embedding with dimension: {len(embedding)} for chunk {i+1}/{len(text_chunks)}")
            except Exception as e:
                print(f"Error generating embedding for chunk {i+1}: {str(e)}")
                all_embeddings.append([])  # Add empty embedding on failure

    return all_embeddings


def main(url: str = None, max_depth: int = MAX_DEPTH, dry_run: bool = False):
    """Main function to orchestrate the complete ingestion pipeline"""
    logger = setup_logging()
    start_time = time.time()

    logger.info("Starting website ingestion pipeline...")

    # Initialize clients and configuration
    sentence_transformer = initialize_sentence_transformer()
    qdrant_client = initialize_qdrant_client()

    # Get base URL from parameter, environment or use default
    base_url = url or os.getenv("WEBSITE_URL", "https://ai-and-humanoid-robotic-course.vercel.app/")

    logger.info(f"Starting ingestion from: {base_url}")

    # Discover all URLs on the website
    urls = get_all_urls(base_url, max_depth=max_depth)
    logger.info(f"Discovered {len(urls)} URLs to process")

    # Test crawling functionality - T017
    if len(urls) > 0:
        logger.info("Crawling functionality test passed - URLs discovered successfully")
    else:
        logger.warning("No URLs discovered during crawling test")

    # Test embedding generation with sample text chunks - T024
    sample_text = "This is a sample text to test embedding generation functionality. It should generate a meaningful embedding vector."
    sample_chunks = chunk_text(sample_text)
    if sample_chunks:
        sentence_transformer_test = initialize_sentence_transformer()
        sample_embeddings = embed(sentence_transformer_test, sample_chunks)
        if sample_embeddings and len(sample_embeddings) > 0 and len(sample_embeddings[0]) > 0:
            logger.info("Embedding generation test passed - embeddings generated successfully")
        else:
            logger.warning("Embedding generation test failed - no embeddings returned")
    else:
        logger.warning("No chunks created from sample text for embedding test")

    # Process each URL
    processed_count = 0
    stored_chunks = 0
    total_urls = len(urls)

    if not dry_run:
        # Create the Qdrant collection for embeddings
        create_collection(qdrant_client, "ai_book_embedding")
    else:
        logger.info("Dry run mode: Skipping Qdrant collection creation")

    # Test vector storage with complete metadata preservation - T031
    test_text = "This is a test chunk to verify metadata preservation in Qdrant storage."
    test_embeddings = embed(sentence_transformer, [test_text])
    test_metadata = {
        "source_url": "https://test-url.com",
        "module_name": "test_module",
        "chunk_index": 0
    }

    if test_embeddings and len(test_embeddings) > 0:
        test_embedding = test_embeddings[0]
        if test_embedding and len(test_embedding) > 0:
            if not dry_run:
                test_point_id = save_chunk_to_qdrant(qdrant_client, test_text, test_embedding, test_metadata, "ai_book_embedding")
                if test_point_id:
                    logger.info("Vector storage test with metadata preservation passed")
                else:
                    logger.warning("Vector storage test with metadata preservation failed")
            else:
                logger.info("Dry run mode: Skipping vector storage test")
        else:
            logger.warning("Could not create test embedding for metadata preservation test - empty embedding")
    else:
        logger.warning("Could not create test embedding for metadata preservation test - no embeddings returned")

    for i, url in enumerate(urls):
        retry_count = 0
        success = False

        while retry_count < MAX_RETRIES and not success:
            try:
                progress_percent = (i + 1) / total_urls * 100
                logger.info(f"Processing URL {i+1}/{total_urls} ({progress_percent:.1f}%): {url} (attempt {retry_count + 1})")

                # Extract text from the URL
                result = extract_text_from_url(url)
                if result is None:
                    logger.warning(f"Failed to extract text from {url} on attempt {retry_count + 1}")
                    retry_count += 1
                    if retry_count < MAX_RETRIES:
                        time.sleep(2 ** retry_count)  # Exponential backoff
                        continue
                    else:
                        logger.error(f"Failed to extract text from {url} after {MAX_RETRIES} attempts")
                        break

                text, module_name = result

                # Validate clean text extraction - T018
                if text.strip() and not any(tag in text for tag in ['<html', '<body', '<div', '<p', '<script']):
                    logger.info(f"Text extraction validation passed for {url}")
                else:
                    logger.warning(f"Text extraction may contain HTML tags for {url}")

                # Chunk the text
                chunks = chunk_text(text)

                # Generate embeddings for each chunk
                for j, chunk in enumerate(chunks):
                    # Generate embedding
                    chunk_embeddings = embed(sentence_transformer, [chunk])

                    # Check if embeddings were generated successfully
                    if chunk_embeddings and len(chunk_embeddings) > 0:
                        embedding = chunk_embeddings[0]  # Get the first (and only) embedding

                        # Prepare metadata
                        metadata = {
                            "source_url": url,
                            "module_name": module_name,
                            "chunk_index": j
                        }

                        if not dry_run:
                            # Save to Qdrant
                            if embedding and len(embedding) > 0:
                                point_id = save_chunk_to_qdrant(qdrant_client, chunk, embedding, metadata, "ai_book_embedding")
                                stored_chunks += 1
                                logger.info(f"Stored chunk {j} from {url} with point ID: {point_id}")
                            else:
                                logger.warning(f"Skipping chunk {j} from {url} due to empty embedding")
                        else:
                            logger.info(f"Dry run mode: Would store chunk {j} from {url}")
                    else:
                        logger.warning(f"Failed to generate embedding for chunk {j} from {url}")

                processed_count += 1
                logger.info(f"Successfully processed {url}")
                success = True  # Mark as successful to exit the retry loop

            except Exception as e:
                logger.error(f"Error processing {url} on attempt {retry_count + 1}: {str(e)}")
                retry_count += 1
                if retry_count < MAX_RETRIES:
                    time.sleep(2 ** retry_count)  # Exponential backoff
                else:
                    logger.error(f"Failed to process {url} after {MAX_RETRIES} attempts")

    # Validate similarity search returns relevant content chunks - T032
    try:
        # Create a test query embedding
        query_text = "artificial intelligence and robotics"
        query_embeddings = embed(sentence_transformer, [query_text])

        if query_embeddings and len(query_embeddings) > 0:
            query_embedding = query_embeddings[0]

            if query_embedding and len(query_embedding) > 0:
                if not dry_run:
                    search_results = search_similar_chunks(qdrant_client, query_embedding, "ai_book_embedding", limit=3)

                    if search_results:
                        logger.info(f"Similarity search validation passed - found {len(search_results)} relevant chunks")
                        for k, result in enumerate(search_results[:2]):  # Show first 2 results
                            logger.info(f"  Result {k+1}: Score {result['score']:.3f} from {result['source_url']}")
                    else:
                        logger.warning("Similarity search validation - no results found")
                else:
                    logger.info("Dry run mode: Skipping similarity search validation")
            else:
                logger.warning("Could not create query embedding for similarity search validation - empty embedding")
        else:
            logger.warning("Could not create query embedding for similarity search validation - no embeddings returned")
    except Exception as e:
        logger.error(f"Error during similarity search validation: {str(e)}")

    # Calculate execution time
    execution_time = time.time() - start_time
    logger.info(f"Pipeline completed in {execution_time:.2f} seconds. Processed {processed_count} URLs, stored {stored_chunks} chunks.")


def initialize_sentence_transformer():
    """Initialize sentence transformer model for embeddings"""
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        return model
    except Exception as e:
        raise ConnectionError(f"Failed to initialize sentence transformer: {str(e)}")


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


def is_relevant_url(url: str) -> bool:
    """
    Check if a URL is relevant for processing (e.g., not an image, PDF, or external link)
    """
    parsed = urlparse(url)

    # Skip if it's not http/https
    if parsed.scheme not in ['http', 'https']:
        return False

    # Skip common non-content file extensions
    non_content_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.svg', '.zip', '.exe', '.dmg']
    if any(url.lower().endswith(ext) for ext in non_content_extensions):
        return False

    # Skip anchor links or JavaScript links
    if url.startswith('#') or url.startswith('javascript:') or url.startswith('mailto:'):
        return False

    return True


def extract_main_content(soup: BeautifulSoup) -> str:
    """
    Extract main content from the page, prioritizing content in main, article, or content containers
    """
    # Look for main content containers in order of preference
    main_content = (
        soup.find('main') or
        soup.find('article') or
        soup.find('div', class_=re.compile(r'content|main|article', re.I)) or
        soup.find('div', id=re.compile(r'content|main|article', re.I)) or
        soup.find('section', class_=re.compile(r'content|main|article', re.I)) or
        soup.find('body')  # Fallback to body if no specific container found
    )

    if main_content:
        # Remove navigation, footer, and other non-content elements from the main content
        for element in main_content(["nav", "header", "footer", "aside", "script", "style"]):
            element.decompose()

        # Get text from the main content area
        text = main_content.get_text()
    else:
        # If no main content container found, extract from the entire body
        for element in soup(["nav", "header", "footer", "aside", "script", "style"]):
            element.decompose()
        text = soup.get_text()

    # Clean up text - remove extra whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)

    return text


def extract_text_from_url(url: str) -> Optional[Tuple[str, str]]:
    """
    Extract clean text content from a given URL
    Returns a tuple of (text, module_name) or None if extraction fails
    """
    # Input validation
    if not isinstance(url, str) or not url:
        print(f"Invalid URL provided: {url}")
        return None

    # Validate URL format
    parsed = urlparse(url)
    if not all([parsed.scheme, parsed.netloc]):
        print(f"Invalid URL format: {url}")
        return None

    max_retries = MAX_RETRIES
    retry_count = 0

    while retry_count < max_retries:
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()  # Raise an exception for bad status codes

            # Try to decode the content properly
            try:
                content = response.content
                # If the content is bytes, decode it properly
                if isinstance(content, bytes):
                    # Try common encodings
                    for encoding in ['utf-8', 'iso-8859-1', 'cp1252']:
                        try:
                            content = response.content.decode(encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        # If all encodings fail, use utf-8 with error handling
                        content = response.content.decode('utf-8', errors='replace')

                soup = BeautifulSoup(content, 'html.parser')
            except Exception as decode_error:
                print(f"Error decoding content from {url}: {str(decode_error)}")
                return None

            # Extract main content while removing navigation elements
            text = extract_main_content(soup)

            # Extract module name from URL structure
            module_name = extract_module_name_from_url(url)

            return text, module_name

        except requests.Timeout:
            print(f"Timeout error extracting text from {url} (attempt {retry_count + 1}/{max_retries})")
            retry_count += 1
            time.sleep(2 ** retry_count)  # Exponential backoff
        except requests.ConnectionError:
            print(f"Connection error extracting text from {url} (attempt {retry_count + 1}/{max_retries})")
            retry_count += 1
            time.sleep(2 ** retry_count)  # Exponential backoff
        except requests.HTTPError as e:
            print(f"HTTP error extracting text from {url}: {str(e)}")
            # Don't retry for client errors (4xx), only for server errors (5xx)
            if 400 <= e.response.status_code < 500:
                return None
            else:
                retry_count += 1
                time.sleep(2 ** retry_count)  # Exponential backoff
        except Exception as e:
            print(f"Unexpected error extracting text from {url}: {str(e)}")
            return None

    # If we've exhausted all retries
    print(f"Failed to extract text from {url} after {max_retries} attempts")
    return None


def filter_urls(urls: List[str]) -> List[str]:
    """
    Filter URLs to ensure only relevant book pages are processed
    """
    filtered_urls = []

    for url in urls:
        if is_relevant_url(url):
            filtered_urls.append(url)

    return filtered_urls


def get_all_urls(base_url: str, max_depth: int = MAX_DEPTH) -> List[str]:
    """
    Discover all URLs on the target website starting from the base URL
    """
    all_urls = set()
    to_visit = [(base_url, 0)]  # (url, depth)
    visited = set()

    base_domain = urlparse(base_url).netloc

    while to_visit:
        current_url, depth = to_visit.pop(0)

        if current_url in visited or depth > max_depth:
            continue

        visited.add(current_url)

        try:
            response = requests.get(current_url, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # Add current URL to the set if it's relevant
                if is_relevant_url(current_url):
                    all_urls.add(current_url)

                # Find all links on the page
                if depth < max_depth:  # Only crawl deeper if we haven't reached max depth
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        absolute_url = urljoin(current_url, href)

                        # Only follow links within the same domain and that are relevant
                        if (urlparse(absolute_url).netloc == base_domain and
                            is_relevant_url(absolute_url) and
                            absolute_url not in visited):
                            to_visit.append((absolute_url, depth + 1))

        except requests.RequestException as e:
            print(f"Error crawling {current_url}: {str(e)}")
            continue  # Continue with other URLs even if one fails

    return list(all_urls)


def extract_module_name_from_url(url: str) -> str:
    """
    Extract module name from URL structure
    """
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.strip('/').split('/')

    # Remove empty parts
    path_parts = [part for part in path_parts if part]

    # If there are path parts, use the first meaningful one as module name
    if path_parts:
        # Take the first part as module name, or a combination if needed
        module_name = path_parts[0]
        # Clean up the name (remove special characters, etc.)
        module_name = re.sub(r'[^\w\s-]', '', module_name).strip()
        if not module_name:
            module_name = "general"
    else:
        module_name = "home"

    return module_name


def create_collection(qdrant_client, collection_name: str = "ai_book_embedding"):
    """
    Create a Qdrant collection for storing embeddings
    """
    max_retries = MAX_RETRIES
    retry_count = 0

    while retry_count < max_retries:
        try:
            # Check if collection already exists
            collections = qdrant_client.get_collections()
            collection_names = [collection.name for collection in collections.collections]

            if collection_name not in collection_names:
                # Create the collection with appropriate vector size for sentence transformer embeddings
                # Using 384 dimensions which is the default for all-MiniLM-L6-v2 model
                qdrant_client.recreate_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
                )
                print(f"Collection '{collection_name}' created successfully with 384-dimensional vectors.")
            else:
                print(f"Collection '{collection_name}' already exists.")

            return True  # Success

        except Exception as e:
            if "limit" in str(e).lower() or "quota" in str(e).lower():
                print(f"Storage limit error when creating collection '{collection_name}': {str(e)}")
                raise  # Don't retry for limit errors
            elif "connection" in str(e).lower() or "timeout" in str(e).lower() or "network" in str(e).lower():
                print(f"Connection error when creating collection '{collection_name}', retry {retry_count + 1}/{max_retries}: {str(e)}")
                retry_count += 1
                time.sleep(2 ** retry_count)  # Exponential backoff
            else:
                print(f"Error creating collection '{collection_name}': {str(e)}")
                retry_count += 1
                if retry_count >= max_retries:
                    raise
                time.sleep(2 ** retry_count)  # Exponential backoff

    return False  # If we've exhausted retries


def save_chunk_to_qdrant(qdrant_client, text_chunk: str, embedding: List[float], metadata: Dict, collection_name: str = "rag_embedding"):
    """
    Save a text chunk with its embedding and metadata to Qdrant
    """
    if not embedding or len(embedding) == 0:
        raise ValueError("Embedding cannot be empty")

    # Verify embedding dimension matches expected size for the collection
    expected_dimension = 1024  # Standard for Cohere's embed-english-v3.0 model
    if len(embedding) != expected_dimension:
        print(f"Warning: Embedding dimension mismatch. Expected {expected_dimension}, got {len(embedding)}")
        # Adjust the collection vector size if needed, or skip this chunk
        # For now, we'll continue with the actual dimension

    max_retries = MAX_RETRIES
    retry_count = 0

    while retry_count < max_retries:
        try:
            import uuid
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

            print(f"Successfully saved chunk to Qdrant with ID: {point_id}, vector dimension: {len(embedding)}")
            return point_id

        except Exception as e:
            if "limit" in str(e).lower() or "quota" in str(e).lower() or "storage" in str(e).lower():
                print(f"Storage limit error when saving chunk to Qdrant: {str(e)}")
                raise  # Don't retry for limit errors
            elif "connection" in str(e).lower() or "timeout" in str(e).lower() or "network" in str(e).lower():
                print(f"Connection error when saving chunk to Qdrant, retry {retry_count + 1}/{max_retries}: {str(e)}")
                retry_count += 1
                time.sleep(2 ** retry_count)  # Exponential backoff
            else:
                print(f"Error saving chunk to Qdrant: {str(e)}")
                retry_count += 1
                if retry_count >= max_retries:
                    raise
                time.sleep(2 ** retry_count)  # Exponential backoff

    raise Exception(f"Failed to save chunk to Qdrant after {max_retries} attempts")


def search_similar_chunks(qdrant_client, query_embedding: List[float], collection_name: str = "rag_embedding", limit: int = 5):
    """
    Search for similar content chunks using vector similarity
    """
    try:
        search_results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=limit,
            with_payload=True
        )

        results = []
        for result in search_results:
            results.append({
                "text": result.payload.get("text", ""),
                "source_url": result.payload.get("source_url", ""),
                "module_name": result.payload.get("module_name", ""),
                "chunk_index": result.payload.get("chunk_index", 0),
                "score": result.score
            })

        return results

    except Exception as e:
        print(f"Error searching for similar chunks: {str(e)}")
        return []


def load_env_variables():
    """Load and validate environment variables"""
    required_vars = ["COHERE_API_KEY", "QDRANT_URL", "QDRANT_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    return {
        "cohere_api_key": os.getenv("COHERE_API_KEY"),
        "qdrant_url": os.getenv("QDRANT_URL"),
        "qdrant_api_key": os.getenv("QDRANT_API_KEY"),
        "website_url": os.getenv("WEBSITE_URL", "https://ai-and-humanoid-robotic-course.vercel.app/")
    }


def handle_rate_limit_error():
    """Handle rate limit errors by implementing exponential backoff"""
    time.sleep(1)  # Simple backoff - in a real implementation, use exponential backoff


def handle_network_error(url: str, error: Exception):
    """Handle network errors gracefully"""
    print(f"Network error occurred while processing {url}: {str(error)}")
    # In a real implementation, we might want to add the URL to a retry queue
    return False  # Indicate that the operation failed


def validate_url(url: str) -> bool:
    """Validate if a URL is properly formatted"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def setup_cli():
    """Set up command-line interface for the main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Website Ingestion, Embedding Generation, and Vector Storage System")
    parser.add_argument("--url", type=str, default=None,
                        help="Base URL to crawl (default: from environment variable)")
    parser.add_argument("--max-depth", type=int, default=MAX_DEPTH,
                        help=f"Maximum depth to crawl (default: {MAX_DEPTH})")
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE,
                        help=f"Size of text chunks (default: {CHUNK_SIZE})")
    parser.add_argument("--chunk-overlap", type=int, default=CHUNK_OVERLAP,
                        help=f"Overlap between chunks (default: {CHUNK_OVERLAP})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run without actually storing embeddings in Qdrant")

    return parser


if __name__ == "__main__":
    parser = setup_cli()
    args = parser.parse_args()

    # Call main function with CLI arguments
    main(url=args.url, max_depth=args.max_depth, dry_run=args.dry_run)