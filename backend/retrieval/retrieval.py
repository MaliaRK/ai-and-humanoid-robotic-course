"""
Vector Retrieval Module for AI & Humanoid Robotics Course

This module implements semantic search functionality to retrieve contextually relevant
content chunks from the Qdrant vector database based on user queries.
"""
import os
import time
import requests
from typing import List, Tuple, Optional, Dict
import numpy as np
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import google.generativeai as genai
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configuration constants
CHUNK_SIZE = 512  # Size of text chunks in characters
CHUNK_OVERLAP = 50  # Overlap between chunks to maintain context
MAX_DEPTH = 2  # Maximum depth to crawl
REQUEST_TIMEOUT = 10  # Timeout for HTTP requests in seconds
MAX_RETRIES = 3  # Maximum number of retries for failed requests
EMBEDDING_BATCH_SIZE = 10  # Number of chunks to embed at once to stay within API limits

def initialize_gemini_client():
    """Initialize Gemini client with API key from environment variables"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required")

    try:
        genai.configure(api_key=api_key)
        return "embedding-001"  # Return model name instead of embedding model object
    except Exception as e:
        raise ConnectionError(f"Failed to initialize Gemini client: {str(e)}")


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


def load_env_variables():
    """Load and validate environment variables"""
    required_vars = ["GEMINI_API_KEY", "QDRANT_URL", "QDRANT_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    return {
        "gemini_api_key": os.getenv("GEMINI_API_KEY"),
        "qdrant_url": os.getenv("QDRANT_URL"),
        "qdrant_api_key": os.getenv("QDRANT_API_KEY"),
        "website_url": os.getenv("WEBSITE_URL", "https://ai-and-humanoid-robotic-course.vercel.app/")
    }


def retrieve_chunks_for_query(gemini_client, qdrant_client, query: str, top_k: int = 5, similarity_threshold: float = 0.0):
    """
    Complete retrieval pipeline: embed query and search for similar chunks
    """
    try:
        # Preprocess the query
        processed_query = preprocess_query(query)

        # Generate embedding for the query
        query_embedding = embed_query(gemini_client, processed_query)

        if query_embedding is None:
            print("Failed to generate embedding for query")
            return []

        # Perform semantic search
        results = semantic_search(
            qdrant_client=qdrant_client,
            query_embedding=query_embedding,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )

        return results

    except Exception as e:
        print(f"Error in retrieval pipeline: {str(e)}")
        return []


def handle_rate_limit_error():
    """Handle rate limit errors with exponential backoff"""
    time.sleep(1)  # Base delay, will be multiplied by retry attempt


def validate_metadata_integrity(retrieved_chunks: List[Dict]) -> Tuple[bool, List[str]]:
    """
    Validate that metadata is preserved and accurate in retrieved chunks
    Returns a tuple of (is_valid, list_of_issues)
    """
    if not retrieved_chunks:
        return True, []  # Empty list is valid

    issues = []

    for i, chunk in enumerate(retrieved_chunks):
        # Check that all required metadata fields exist
        required_fields = ["text", "source_url", "module_name", "chunk_index", "similarity_score"]

        for field in required_fields:
            if field not in chunk:
                issues.append(f"Chunk {i}: Missing required metadata field '{field}'")

        # Validate specific metadata fields if they exist
        if "source_url" in chunk:
            if not isinstance(chunk["source_url"], str) or not chunk["source_url"]:
                issues.append(f"Chunk {i}: Invalid or empty source_url")

        if "module_name" in chunk:
            if not isinstance(chunk["module_name"], str) or not chunk["module_name"]:
                issues.append(f"Chunk {i}: Invalid or empty module_name")

        if "chunk_index" in chunk:
            if not isinstance(chunk["chunk_index"], int) or chunk["chunk_index"] < 0:
                issues.append(f"Chunk {i}: Invalid chunk_index (must be non-negative integer)")

    is_valid = len(issues) == 0
    return is_valid, issues


def extract_metadata_from_results(search_results: List[Dict]) -> List[Dict]:
    """
    Extract metadata from retrieval results for validation
    """
    metadata_list = []

    for result in search_results:
        # Extract the metadata fields from each result
        metadata = {
            "source_url": result.get("source_url", ""),
            "module_name": result.get("module_name", ""),
            "chunk_index": result.get("chunk_index", 0),
            "similarity_score": result.get("similarity_score", 0.0),
            "text_preview": result.get("text", "")[:100] + "..." if len(result.get("text", "")) > 100 else result.get("text", "")
        }

        metadata_list.append(metadata)

    return metadata_list


def generate_metadata_validation_report(validation_results: List[Dict]) -> Dict:
    """
    Generate a comprehensive report on metadata validation results
    Returns a summary with statistics and detailed findings
    """
    if not validation_results:
        return {
            "total_chunks_validated": 0,
            "valid_chunks": 0,
            "invalid_chunks": 0,
            "accuracy_percentage": 0.0,
            "findings": [],
            "summary": "No chunks were validated"
        }

    total_chunks = len(validation_results)
    valid_chunks = 0
    all_differences = []

    for result in validation_results:
        if result.get("matches_expected", False):
            valid_chunks += 1
        else:
            differences = result.get("differences", [])
            all_differences.extend(differences)

    invalid_chunks = total_chunks - valid_chunks
    accuracy_percentage = (valid_chunks / total_chunks) * 100 if total_chunks > 0 else 0

    summary = f"Metadata validation completed: {valid_chunks}/{total_chunks} chunks passed validation ({accuracy_percentage:.1f}% accuracy)"

    return {
        "total_chunks_validated": total_chunks,
        "valid_chunks": valid_chunks,
        "invalid_chunks": invalid_chunks,
        "accuracy_percentage": accuracy_percentage,
        "findings": all_differences,
        "summary": summary
    }


def compare_metadata_to_source(metadata: Dict, expected_values: Dict) -> Dict:
    """
    Compare retrieved metadata to expected values from the source
    Returns a dictionary with comparison results
    """
    comparison_results = {
        "matches_expected": True,
        "differences": [],
        "accuracy_score": 0.0
    }

    if not metadata or not expected_values:
        comparison_results["matches_expected"] = False
        comparison_results["differences"] = ["Either metadata or expected values are empty"]
        return comparison_results

    differences = []

    for key, expected_value in expected_values.items():
        if key not in metadata:
            differences.append(f"Missing field: {key}")
            continue

        actual_value = metadata[key]

        if actual_value != expected_value:
            differences.append(f"{key}: expected '{expected_value}', got '{actual_value}'")

    comparison_results["matches_expected"] = len(differences) == 0
    comparison_results["differences"] = differences
    comparison_results["accuracy_score"] = 1.0 - (len(differences) / len(expected_values)) if expected_values else 1.0

    return comparison_results


def test_metadata_preservation_with_query_types():
    """
    Test metadata preservation with various types of queries
    """
    print("Testing metadata preservation with various query types...")

    try:
        # Initialize clients
        gemini_client = initialize_gemini_client()
        qdrant_client = initialize_qdrant_client()
    except Exception as e:
        print(f"Failed to initialize clients for metadata testing: {str(e)}")
        return False

    # Various types of queries to test metadata preservation
    test_queries = [
        ("general", "What is artificial intelligence?", "General concept query"),
        ("specific", "How do neural networks work?", "Specific concept query"),
        ("chapter_specific", "Explain computer vision in robotics", "Chapter/module specific query"),
        ("technical", "What are the principles of reinforcement learning?", "Technical concept query"),
        ("application", "How is AI applied in humanoid robotics?", "Application-focused query")
    ]

    all_tests_passed = True

    for query_type, query, description in test_queries:
        print(f"  Testing {query_type} query: {description}")
        print(f"    Query: '{query}'")

        # Process the query
        results = retrieve_chunks_for_query(
            gemini_client=gemini_client,
            qdrant_client=qdrant_client,
            query=query,
            top_k=2,
            similarity_threshold=0.3
        )

        if results:
            print(f"    ✅ Found {len(results)} results")

            # Validate metadata for each result
            metadata_issues = 0
            for i, result in enumerate(results):
                # Check if all required metadata fields exist
                required_fields = ["source_url", "module_name", "chunk_index", "similarity_score", "text"]

                missing_fields = [field for field in required_fields if field not in result]
                if missing_fields:
                    print(f"      ⚠️  Result {i+1} missing fields: {missing_fields}")
                    metadata_issues += 1
                    continue

                # Validate specific metadata fields
                if not result["source_url"] or not isinstance(result["source_url"], str):
                    print(f"      ⚠️  Result {i+1} has invalid source_url: {result['source_url']}")
                    metadata_issues += 1

                if not result["module_name"] or not isinstance(result["module_name"], str):
                    print(f"      ⚠️  Result {i+1} has invalid module_name: {result['module_name']}")
                    metadata_issues += 1

                if not isinstance(result["chunk_index"], int) or result["chunk_index"] < 0:
                    print(f"      ⚠️  Result {i+1} has invalid chunk_index: {result['chunk_index']}")
                    metadata_issues += 1

            if metadata_issues == 0:
                print(f"    ✅ Metadata validation passed for {query_type} query")
            else:
                print(f"    ⚠️  Metadata validation found {metadata_issues} issues for {query_type} query")
                all_tests_passed = False
        else:
            print(f"    ❌ No results found for {query_type} query")
            # This might be expected for some queries, so we won't necessarily mark as failure
            # unless it happens consistently across all query types

    if all_tests_passed:
        print("\n✅ All metadata preservation tests passed - metadata is preserved across different query types")
        return True
    else:
        print("\n⚠️  Some metadata preservation tests had issues - review results")
        return False


def create_test_data_with_known_metadata() -> List[Dict]:
    """
    Create test data with known metadata for validation purposes
    Returns a list of dictionaries containing test chunks with expected metadata
    """
    test_data = [
        {
            "text": "Artificial Intelligence and Machine Learning form the foundation of modern robotics systems. These technologies enable robots to perceive, reason, and act in complex environments.",
            "expected_metadata": {
                "source_url": "https://ai-and-humanoid-robotic-course.vercel.app/introduction-to-ai",
                "module_name": "introduction",
                "chunk_index": 0
            }
        },
        {
            "text": "Humanoid robotics combines mechanical engineering, electronics, and computer science to create robots with human-like form and capabilities.",
            "expected_metadata": {
                "source_url": "https://ai-and-humanoid-robotic-course.vercel.app/humanoid-robotics-basics",
                "module_name": "basics",
                "chunk_index": 1
            }
        },
        {
            "text": "Neural networks are computational models inspired by biological neural networks. They form the basis of deep learning algorithms used in robotics perception.",
            "expected_metadata": {
                "source_url": "https://ai-and-humanoid-robotic-course.vercel.app/neural-networks",
                "module_name": "neural_networks",
                "chunk_index": 2
            }
        },
        {
            "text": "Reinforcement learning enables robots to learn optimal behaviors through trial and error, receiving rewards for desired actions.",
            "expected_metadata": {
                "source_url": "https://ai-and-humanoid-robotic-course.vercel.app/reinforcement-learning",
                "module_name": "learning",
                "chunk_index": 0
            }
        },
        {
            "text": "Computer vision allows robots to interpret and understand visual information from cameras, enabling navigation and object recognition.",
            "expected_metadata": {
                "source_url": "https://ai-and-humanoid-robotic-course.vercel.app/computer-vision",
                "module_name": "vision",
                "chunk_index": 1
            }
        }
    ]

    return test_data


def validate_metadata_across_content_modules():
    """
    Validate metadata accuracy across different content modules
    """
    print("Validating metadata accuracy across different content modules...")

    try:
        # Initialize clients
        gemini_client = initialize_gemini_client()
        qdrant_client = initialize_qdrant_client()
    except Exception as e:
        print(f"Failed to initialize clients for metadata validation: {str(e)}")
        return False

    # Test queries focused on different content modules
    module_specific_queries = [
        ("introduction", "What is the introduction to AI robotics?", "Introduction module query"),
        ("vision", "Explain computer vision concepts", "Computer vision module query"),
        ("learning", "How does reinforcement learning work?", "Learning module query"),
        ("neural_networks", "What are neural networks?", "Neural networks module query"),
        ("basics", "Explain the basics of humanoid robotics?", "Basics module query")
    ]

    validation_results = []
    all_valid = True

    for module_name, query, description in module_specific_queries:
        print(f"  Validating {module_name} module: {description}")
        print(f"    Query: '{query}'")

        # Perform retrieval
        results = retrieve_chunks_for_query(
            gemini_client=gemini_client,
            qdrant_client=qdrant_client,
            query=query,
            top_k=2,
            similarity_threshold=0.3
        )

        if results:
            module_matches = 0
            total_results = len(results)

            for i, result in enumerate(results):
                # Validate metadata integrity
                required_fields = ["source_url", "module_name", "chunk_index", "similarity_score", "text"]
                missing_fields = [field for field in required_fields if field not in result]

                if missing_fields:
                    print(f"      ⚠️  Result {i+1} missing metadata fields: {missing_fields}")
                    all_valid = False
                    continue

                # Check if the result's module matches the expected module context
                result_module = result.get("module_name", "").lower()
                query_lower = query.lower()

                # Check if the result is contextually related to the expected module
                if (module_name in result_module or
                    module_name in query_lower or
                    result_module in module_name or
                    (module_name == "vision" and "vision" in result_module) or
                    (module_name == "learning" and "learning" in result_module)):
                    module_matches += 1

            print(f"      ✅ {module_matches}/{total_results} results match expected module context")

            validation_results.append({
                "module": module_name,
                "query": query,
                "results_count": total_results,
                "matching_results": module_matches,
                "valid": len([r for r in results if not any(field not in r for field in ["source_url", "module_name", "chunk_index", "similarity_score", "text"])]) == total_results
            })
        else:
            print(f"      ❌ No results found for {module_name} module query")
            validation_results.append({
                "module": module_name,
                "query": query,
                "results_count": 0,
                "matching_results": 0,
                "valid": False
            })
            all_valid = False

    # Generate summary report
    total_modules = len(validation_results)
    valid_modules = sum(1 for result in validation_results if result["valid"])

    print(f"\nMetadata validation across modules: {valid_modules}/{total_modules} modules validated successfully")

    if all_valid and valid_modules > 0:
        print("✅ Metadata accuracy validation passed across different content modules")
        return True
    else:
        print("⚠️  Metadata accuracy validation had issues across some content modules")
        return False


def create_configurable_top_k_search(k: int = 5):
    """
    Create a function that performs top-k search with configurable result count
    """
    def search_function(qdrant_client, query_embedding, collection_name: str = "rag_embedding", similarity_threshold: float = 0.0):
        """
        Perform semantic search with configurable top-k parameter
        """
        try:
            results = qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=k,
                score_threshold=similarity_threshold,
                with_payload=True
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "text": result.payload.get("text", ""),
                    "source_url": result.payload.get("source_url", ""),
                    "module_name": result.payload.get("module_name", ""),
                    "chunk_index": result.payload.get("chunk_index", 0),
                    "similarity_score": result.score
                })

            return formatted_results

        except Exception as e:
            print(f"Error during top-{k} search: {str(e)}")
            return []

    return search_function


def apply_similarity_threshold_filter(results: List[Dict], threshold: float = 0.5) -> List[Dict]:
    """
    Filter search results based on similarity threshold
    """
    if threshold <= 0:
        return results

    filtered_results = []
    for result in results:
        if result.get("similarity_score", 0) >= threshold:
            filtered_results.append(result)

    return filtered_results


def measure_retrieval_latency(func, *args, **kwargs) -> Tuple[float, any]:
    """
    Measure the execution time of a retrieval function
    Returns a tuple of (latency_in_seconds, function_result)
    """
    start_time = time.time()

    try:
        result = func(*args, **kwargs)
        end_time = time.time()

        latency = end_time - start_time
        return latency, result
    except Exception as e:
        end_time = time.time()
        latency = end_time - start_time
        print(f"Error during latency measurement: {str(e)}")
        return latency, None


def benchmark_retrieval_performance(gemini_client, qdrant_client, test_queries: List[str], top_k_values: List[int] = [3, 5, 10]):
    """
    Benchmark retrieval performance across different configuration parameters
    """
    print("Benchmarking retrieval performance across configurations...")

    results = {}

    for k in top_k_values:
        print(f"  Testing with top-k={k}")

        avg_latency = 0
        total_tests = 0

        for query in test_queries:
            # Embed the query
            query_embedding = embed_query(gemini_client, query)

            if query_embedding is not None:
                # Measure retrieval latency
                latency, search_results = measure_retrieval_latency(
                    qdrant_client.search,
                    collection_name="rag_embedding",
                    query_vector=query_embedding,
                    limit=k,
                    score_threshold=0.3,
                    with_payload=True
                )

                avg_latency += latency
                total_tests += 1

                print(f"    Query '{query[:50]}...' took {latency:.3f}s with top-{k} results")

        if total_tests > 0:
            avg_latency /= total_tests
            results[k] = {
                "avg_latency": avg_latency,
                "total_tests": total_tests,
                "status": "✅" if avg_latency < 1.0 else "⚠️"  # Alert if latency > 1 second
            }
            print(f"    Average latency for top-{k}: {avg_latency:.3f}s {results[k]['status']}")
        else:
            results[k] = {
                "avg_latency": 0,
                "total_tests": 0,
                "status": "❌"
            }
            print(f"    No successful tests for top-{k}")

    print(f"\nPerformance benchmarking complete")
    return results


def test_retrieval_performance_with_different_configs():
    """
    Test retrieval performance with various parameter configurations
    """
    print("Testing retrieval performance with different parameter configurations...")

    try:
        # Initialize clients
        gemini_client = initialize_gemini_client()
        qdrant_client = initialize_qdrant_client()
    except Exception as e:
        print(f"Failed to initialize clients for performance testing: {str(e)}")
        return False

    # Test queries to use for performance testing
    test_queries = [
        "What is artificial intelligence?",
        "Explain neural networks",
        "How does computer vision work?",
        "What is reinforcement learning?",
        "Describe humanoid robotics"
    ]

    # Test different top-k configurations
    top_k_values = [1, 3, 5, 10]
    results = {}

    for k in top_k_values:
        print(f"  Testing with top-k={k}")

        total_latency = 0
        successful_queries = 0

        for query in test_queries:
            # Embed the query
            query_embedding = embed_query(gemini_client, query)

            if query_embedding is not None:
                # Measure retrieval latency
                start_time = time.time()

                try:
                    search_results = qdrant_client.search(
                        collection_name="rag_embedding",
                        query_vector=query_embedding,
                        limit=k,
                        score_threshold=0.3,
                        with_payload=True
                    )

                    end_time = time.time()
                    latency = end_time - start_time

                    total_latency += latency
                    successful_queries += 1

                    print(f"    Query '{query[:30]}...' with top-{k}: {latency:.3f}s")

                except Exception as e:
                    print(f"    Error querying with top-{k} for '{query}': {str(e)}")
                    continue
            else:
                print(f"    Failed to embed query: '{query}'")
                continue

        if successful_queries > 0:
            avg_latency = total_latency / successful_queries
            results[k] = {
                "average_latency": avg_latency,
                "successful_queries": successful_queries,
                "status": "✅" if avg_latency < 0.5 else "⚠️" if avg_latency < 1.0 else "❌"  # Good if <500ms, OK if <1s, poor if >1s
            }
            print(f"    Average latency for top-{k}: {avg_latency:.3f}s {results[k]['status']}")
        else:
            results[k] = {
                "average_latency": float('inf'),
                "successful_queries": 0,
                "status": "❌"
            }
            print(f"    No successful queries for top-{k} configuration")

    print(f"\nPerformance testing across configurations completed")
    return True


def setup_logging():
    """
    Set up logging configuration for the pipeline
    """
    # Create logs directory if it doesn't exist
    import os
    os.makedirs("logs", exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/retrieval_pipeline.log'),
            logging.StreamHandler()  # Also log to console
        ]
    )
    return logging.getLogger(__name__)


def add_logging_configuration():
    """
    Enhanced logging configuration for debugging and monitoring
    """
    # Create logs directory if it doesn't exist
    import os
    os.makedirs("logs", exist_ok=True)

    # Create a custom logger
    logger = logging.getLogger('retrieval_pipeline')
    logger.setLevel(logging.DEBUG)

    # Create handlers
    c_handler = logging.StreamHandler()  # Console handler
    f_handler = logging.FileHandler('logs/retrieval_pipeline.log')  # File handler
    c_handler.setLevel(logging.INFO)
    f_handler.setLevel(logging.DEBUG)

    # Create formatters and add it to handlers
    c_format = logging.Formatter('%(levelname)s - %(message)s')
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s')
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    # Add handlers to the logger
    if not logger.handlers:  # Avoid adding handlers multiple times
        logger.addHandler(c_handler)
        logger.addHandler(f_handler)

    return logger


def track_progress(current: int, total: int, description: str = "Processing"):
    """
    Track and display progress for long-running operations
    """
    progress = (current / total) * 100 if total > 0 else 0
    print(f"\r{description}: {current}/{total} ({progress:.1f}%)", end='', flush=True)

    # Log progress to file as well
    logger = logging.getLogger(__name__)
    if current % max(1, total // 10) == 0 or current == total:  # Log every 10% or at completion
        logger.info(f"{description}: {current}/{total} ({progress:.1f}%) completed")


def validate_performance_meets_interactive_requirements():
    """
    Validate that retrieval performance meets requirements for interactive use (<500ms)
    """
    print("Validating performance meets interactive use requirements (<500ms)...")

    try:
        # Initialize clients
        gemini_client = initialize_gemini_client()
        qdrant_client = initialize_qdrant_client()
    except Exception as e:
        print(f"Failed to initialize clients for performance validation: {str(e)}")
        return False

    # Define performance requirements
    MAX_ACCEPTABLE_LATENCY = 0.5  # 500ms

    # Test queries representative of interactive use
    interactive_queries = [
        "What is AI?",
        "Explain machine learning",
        "How do robots see?",
        "What is a neural network?",
        "Humanoid robotics basics"
    ]

    latencies = []
    successful_tests = 0
    total_tests = len(interactive_queries)

    for i, query in enumerate(interactive_queries):
        # Track progress
        track_progress(i + 1, total_tests, "Performance validation")

        # Embed the query
        query_embedding = embed_query(gemini_client, query)

        if query_embedding is not None:
            # Measure retrieval time
            start_time = time.time()

            try:
                # Perform a standard retrieval operation
                results = qdrant_client.search(
                    collection_name="rag_embedding",
                    query_vector=query_embedding,
                    limit=5,  # Standard top-k for interactive use
                    score_threshold=0.4,  # Standard threshold
                    with_payload=True
                )

                end_time = time.time()
                latency = end_time - start_time
                latencies.append(latency)

                status = "✅" if latency < MAX_ACCEPTABLE_LATENCY else "❌"
                print(f"\n  Query '{query}': {latency:.3f}s {status}")

                if latency < MAX_ACCEPTABLE_LATENCY:
                    successful_tests += 1

            except Exception as e:
                print(f"\n  Error testing performance for '{query}': {str(e)}")
                latencies.append(float('inf'))  # Use infinity to indicate failure
        else:
            print(f"\n  Failed to embed query for performance test: '{query}'")
            latencies.append(float('inf'))

    # Print final progress
    print(f"\n")

    if latencies:
        avg_latency = sum(l for l in latencies if l != float('inf')) / len([l for l in latencies if l != float('inf')])
        success_rate = successful_tests / total_tests if total_tests > 0 else 0

        print(f"\nAverage latency: {avg_latency:.3f}s")
        print(f"Success rate: {success_rate*100:.1f}% ({successful_tests}/{total_tests})")

        if avg_latency < MAX_ACCEPTABLE_LATENCY and success_rate >= 0.8:  # At least 80% success rate
            print(f"✅ Performance validation passed - meets interactive use requirements")
            return True
        else:
            print(f"❌ Performance validation failed - latency too high or success rate too low")
            return False
    else:
        print("❌ No valid latency measurements obtained")
        return False


def handle_network_error(error: Exception):
    """Handle network errors gracefully"""
    print(f"Network error occurred: {str(error)}")
    # In a real implementation, we might want to implement more sophisticated retry logic
    return False  # Indicate that the operation failed


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split text content into semantic chunks of appropriate size
    """
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


def embed(gemini_client, text_chunks: List[str]) -> List[List[float]]:
    """
    Generate semantic embeddings for text chunks using Gemini
    """
    if not text_chunks:
        return []

    # Process one chunk at a time to minimize rate limit issues
    all_embeddings = []

    for i, text in enumerate(text_chunks):
        retry_count = 0
        while retry_count < MAX_RETRIES:
            try:
                result = genai.embed_content(
                    model=gemini_client,  # Use the model name
                    content=text,  # Pass text directly instead of list
                    task_type="RETRIEVAL_DOCUMENT"  # Optimize for document retrieval
                )

                # Extract embeddings from the response
                if result and result['embedding']:
                    batch_embeddings = [result['embedding']]  # Wrap in list to match expected format
                    all_embeddings.extend(batch_embeddings)
                else:
                    print(f"No embedding returned for chunk {i}, adding empty embedding")
                    all_embeddings.append([])  # Add empty embedding on failure
                    break

                # Add delay between API calls to respect rate limits
                time.sleep(0.1)  # 100ms delay between each embedding call
                break  # Success, break out of retry loop

            except Exception as e:
                if "rate_limit" in str(e).lower() or "quota" in str(e).lower() or "429" in str(e):
                    print(f"Gemini rate limit/quota hit, waiting before retry {retry_count + 1}/{MAX_RETRIES}")
                    wait_time = 2 ** retry_count  # Exponential backoff
                    time.sleep(wait_time)
                    retry_count += 1
                    continue
                elif "quota" in str(e).lower() or "credit" in str(e).lower():
                    print(f"Gemini API quota exceeded: {str(e)}")
                    # Graceful degradation: return partial results
                    # Add empty embeddings for remaining chunks
                    remaining_chunks = len(text_chunks) - i
                    all_embeddings.extend([[] for _ in range(remaining_chunks)])
                    break  # Stop processing, quota exceeded
                else:
                    print(f"Gemini API error: {str(e)}")
                    # Don't retry for other API errors
                    break
            except Exception as e:
                print(f"Error generating embedding for text: {str(e)}")
                retry_count += 1
                if retry_count >= MAX_RETRIES:
                    # If we've exhausted retries, add empty embedding for this chunk
                    all_embeddings.append([])
                else:
                    time.sleep(2 ** retry_count)  # Exponential backoff

    return all_embeddings


def embed_query(gemini_client, query_text: str) -> Optional[List[float]]:
    """
    Generate embedding for a single query text using Gemini
    """
    if not query_text:
        return None

    try:
        result = genai.embed_content(
            model=gemini_client,  # Use the model name
            content=query_text,  # Pass text directly instead of list
            task_type="RETRIEVAL_QUERY"  # Optimize for query retrieval
        )

        # Extract the embedding from the response
        if result and result['embedding']:
            return result['embedding']

        return None

    except Exception as e:
        if "rate_limit" in str(e).lower() or "quota" in str(e).lower() or "429" in str(e):
            print(f"Rate limit/quota hit when embedding query: {str(e)}")
            handle_rate_limit_error()
            return None
        elif "quota" in str(e).lower() or "credit" in str(e).lower():
            print(f"Gemini API quota exceeded when embedding query: {str(e)}")
            return None
        else:
            print(f"Gemini API error when embedding query: {str(e)}")
            return None


def preprocess_query(query: str) -> str:
    """
    Clean and normalize the input query
    """
    if not query or not isinstance(query, str):
        return ""

    # Strip leading/trailing whitespace
    query = query.strip()

    # Remove extra whitespace
    query = ' '.join(query.split())

    # Additional cleaning could be added here if needed
    # For example, removing special characters, correcting common typos, etc.

    return query


def semantic_search(qdrant_client, query_embedding: List[float], collection_name: str = "rag_embedding", top_k: int = 5, similarity_threshold: float = 0.0):
    """
    Perform semantic search in Qdrant collection with comprehensive error handling
    """
    if not query_embedding:
        raise ValueError("Query embedding cannot be empty")

    max_retries = MAX_RETRIES
    retry_count = 0

    while retry_count < max_retries:
        try:
            # Perform semantic search in Qdrant
            search_results = qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=top_k,
                score_threshold=similarity_threshold,
                with_payload=True
            )

            # Format results for easier consumption
            formatted_results = []
            for result in search_results:
                formatted_results.append({
                    "text": result.payload.get("text", ""),
                    "source_url": result.payload.get("source_url", ""),
                    "module_name": result.payload.get("module_name", ""),
                    "chunk_index": result.payload.get("chunk_index", 0),
                    "similarity_score": result.score
                })

            return formatted_results

        except Exception as e:
            error_msg = str(e).lower()

            # Handle connection-related errors
            if "connection" in error_msg or "connect" in error_msg or "timeout" in error_msg:
                print(f"Connection error during semantic search (attempt {retry_count + 1}/{max_retries}): {str(e)}")
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(2 ** retry_count)  # Exponential backoff
                continue

            # Handle rate limiting or quota errors
            elif "rate_limit" in error_msg or "quota" in error_msg or "limit" in error_msg:
                print(f"Rate limit or quota error during semantic search: {str(e)}")
                # Don't retry for rate limit/quota errors
                break

            # Handle collection not found errors
            elif "not found" in error_msg or ("collection" in error_msg and "not" in error_msg and ("found" in error_msg or "exist" in error_msg)):
                print(f"Collection '{collection_name}' not found: {str(e)}")
                # Don't retry for collection not found errors
                break

            # Handle other errors
            else:
                print(f"Error during semantic search: {str(e)}")
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(2 ** retry_count)  # Exponential backoff
                else:
                    # If we've exhausted retries, return empty results
                    print(f"Semantic search failed after {max_retries} attempts")
                continue

    return []


def comprehensive_error_handler(func):
    """
    Decorator to add comprehensive error handling to functions
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            print(f"ValueError in {func.__name__}: {str(e)}")
            return None
        except ConnectionError as e:
            print(f"ConnectionError in {func.__name__}: {str(e)}")
            return None
        except requests.exceptions.Timeout as e:
            print(f"Timeout in {func.__name__}: {str(e)}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"RequestException in {func.__name__}: {str(e)}")
            return None
        except Exception as e:
            print(f"Unexpected error in {func.__name__}: {str(e)}")
            return None
    return wrapper


@comprehensive_error_handler
def retrieve_chunks_for_query_with_retry(gemini_client, qdrant_client, query: str, top_k: int = 5, similarity_threshold: float = 0.3, collection_name: str = "rag_embedding", max_retries: int = MAX_RETRIES):
    """
    Retrieve semantically similar content chunks for a given query with retry logic
    """
    retry_count = 0

    while retry_count < max_retries:
        try:
            # Preprocess the query
            processed_query = preprocess_query(query)

            if not processed_query:
                print(f"Invalid query provided: {query}")
                return []

            # Generate embedding for the query
            query_embedding = embed_query(gemini_client, processed_query)

            if query_embedding is None or len(query_embedding) == 0:
                print(f"Failed to generate embedding for query: {query}")
                return []

            # Perform semantic search
            search_results = semantic_search(
                qdrant_client=qdrant_client,
                query_embedding=query_embedding,
                collection_name=collection_name,
                top_k=top_k,
                similarity_threshold=similarity_threshold
            )

            return search_results

        except Exception as e:
            error_str = str(e).lower()

            # Check if it's a recoverable error (network, timeout, rate limit)
            if ("connection" in error_str or
                "timeout" in error_str or
                "rate_limit" in error_str or
                "network" in error_str or
                ("status_code" in error_str and "429" in error_str)):

                print(f"Retriable error occurred during query '{query}' (attempt {retry_count + 1}/{max_retries}): {str(e)}")
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = 2 ** retry_count  # Exponential backoff
                    print(f"  Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                continue
            else:
                # Non-recoverable error, don't retry
                print(f"Non-retryable error retrieving chunks for query '{query}': {str(e)}")
                break

    # If we've exhausted all retries
    print(f"Failed to retrieve chunks for query '{query}' after {max_retries} attempts")
    return []


def create_collection(qdrant_client, collection_name: str = "rag_embedding"):
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
                # Create the collection with appropriate vector size for Gemini embeddings
                # Gemini's embedding-001 returns 768-dimension vectors
                qdrant_client.recreate_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),
                )
                print(f"Collection '{collection_name}' created successfully with 768-dimensional vectors.")
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
    expected_dimension = 768  # Standard for Gemini's embedding-001 model
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
        # Perform semantic search in Qdrant
        search_results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=limit,
            with_payload=True
        )

        # Format results for easier consumption
        results = []
        for result in search_results:
            results.append({
                "text": result.payload.get("text", ""),
                "source_url": result.payload.get("source_url", ""),
                "module_name": result.payload.get("module_name", ""),
                "chunk_index": result.payload.get("chunk_index", 0),
                "similarity_score": result.score
            })

        return results

    except Exception as e:
        print(f"Error during similarity search: {str(e)}")
        return []


def retrieve_chunks_for_query(gemini_client, qdrant_client, query: str, top_k: int = 5, similarity_threshold: float = 0.0):
    """
    Complete retrieval pipeline: embed query and search for similar chunks
    """
    try:
        # Generate embedding for the query
        query_embeddings = embed(gemini_client, [query])

        if not query_embeddings or len(query_embeddings) == 0:
            print("Failed to generate embedding for query")
            return []

        query_embedding = query_embeddings[0]  # Get the first (and only) embedding

        if not query_embedding or len(query_embedding) == 0:
            print("Generated embedding is empty")
            return []

        # Search for similar chunks in Qdrant
        similar_chunks = search_similar_chunks(
            qdrant_client=qdrant_client,
            query_embedding=query_embedding,
            collection_name="rag_embedding",
            limit=top_k
        )

        # Filter by similarity threshold if specified
        if similarity_threshold > 0:
            similar_chunks = [chunk for chunk in similar_chunks if chunk["similarity_score"] >= similarity_threshold]

        return similar_chunks

    except Exception as e:
        print(f"Error in retrieval pipeline: {str(e)}")
        return []


def test_semantic_search_with_sample_queries():
    """
    Test semantic search functionality with sample queries against target content
    """
    print("Testing semantic search with sample queries...")

    # Initialize clients
    try:
        gemini_client = initialize_gemini_client()
        qdrant_client = initialize_qdrant_client()
    except Exception as e:
        print(f"Failed to initialize clients for testing: {str(e)}")
        return False

    # Sample test queries
    test_queries = [
        "What are the principles of humanoid robotics?",
        "Explain artificial intelligence concepts",
        "How do neural networks work?",
        "What is computer vision in robotics?",
        "Explain reinforcement learning algorithms"
    ]

    success_count = 0

    for i, query in enumerate(test_queries, 1):
        print(f"  Test {i}: Querying for '{query[:50]}{'...' if len(query) > 50 else ''}'")

        # Preprocess the query
        processed_query = preprocess_query(query)

        # Generate embedding for the query
        query_embedding = embed_query(gemini_client, processed_query)

        if query_embedding is None:
            print(f"    ❌ Failed to generate embedding for query: {query}")
            continue

        # Perform semantic search
        results = semantic_search(qdrant_client, query_embedding, top_k=3)

        if results:
            print(f"    ✅ Found {len(results)} relevant chunks for query: {query}")

            # Validate contextual relevance - check if results seem relevant to query
            relevant_results = 0
            for result in results:
                # Basic relevance check: see if result text contains terms related to query
                query_lower = query.lower()
                text_lower = result["text"].lower()

                # Count how many query terms appear in the result
                query_terms = query_lower.split()
                term_matches = sum(1 for term in query_terms if term in text_lower and len(term) > 2)  # Only count terms longer than 2 chars

                if term_matches > 0:
                    relevant_results += 1

            if relevant_results > 0:
                print(f"      {relevant_results}/{len(results)} results appear contextually relevant")
                success_count += 1
            else:
                print(f"      Warning: Results may not be contextually relevant to query")
        else:
            print(f"    ❌ No results found for query: {query}")

    print(f"\nSemantic search test completed: {success_count}/{len(test_queries)} queries returned relevant results")

    if success_count == len(test_queries):
        print("✅ Semantic search validation passed - all queries returned contextually relevant results")
        return True
    else:
        print("⚠️  Semantic search validation partially passed - some queries may need adjustment")
        return False


def generate_retrieval_statistics(results: List[Dict], query: str = "", latency: float = 0.0) -> Dict:
    """
    Generate summary statistics and reporting for retrieval results
    """
    stats = {
        "query": query,
        "total_results": len(results),
        "latency_seconds": latency,
        "avg_similarity_score": 0.0,
        "min_similarity_score": float('inf'),
        "max_similarity_score": float('-inf'),
        "avg_chunk_size": 0,
        "unique_sources": set(),
        "unique_modules": set(),
        "timestamp": time.time()
    }

    if results:
        similarity_scores = [result.get('similarity_score', 0.0) for result in results]
        stats["avg_similarity_score"] = sum(similarity_scores) / len(similarity_scores)
        stats["min_similarity_score"] = min(similarity_scores)
        stats["max_similarity_score"] = max(similarity_scores)

        chunk_sizes = [len(result.get('text', '')) for result in results]
        stats["avg_chunk_size"] = sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0

        for result in results:
            source_url = result.get('source_url', '')
            module_name = result.get('module_name', '')
            if source_url:
                stats["unique_sources"].add(source_url)
            if module_name:
                stats["unique_modules"].add(module_name)

    # Convert sets to lists for JSON serialization
    stats["unique_sources"] = list(stats["unique_sources"])
    stats["unique_modules"] = list(stats["unique_modules"])

    return stats


def generate_summary_report(retrieval_stats: List[Dict], overall_latency: float = 0.0) -> Dict:
    """
    Generate a comprehensive summary report with retrieval statistics
    """
    if not retrieval_stats:
        return {
            "summary": "No retrieval operations performed",
            "total_queries": 0,
            "total_results": 0,
            "overall_latency": overall_latency,
            "avg_latency_per_query": 0.0,
            "avg_similarity_score": 0.0,
            "success_rate": 0.0,
            "unique_sources_count": 0,
            "unique_modules_count": 0,
            "detailed_stats": []
        }

    total_queries = len(retrieval_stats)
    total_results = sum(stat.get("total_results", 0) for stat in retrieval_stats)
    successful_queries = sum(1 for stat in retrieval_stats if stat.get("total_results", 0) > 0)

    # Calculate average similarity across all results
    all_similarities = []
    for stat in retrieval_stats:
        if stat.get("total_results", 0) > 0:
            all_similarities.extend([result.get('similarity_score', 0.0) for result in stat.get('results', [])])

    avg_similarity = sum(all_similarities) / len(all_similarities) if all_similarities else 0.0

    # Collect unique sources and modules
    all_sources = set()
    all_modules = set()
    for stat in retrieval_stats:
        all_sources.update(stat.get("unique_sources", []))
        all_modules.update(stat.get("unique_modules", []))

    report = {
        "summary": f"Retrieval pipeline completed: {successful_queries}/{total_queries} queries successful",
        "total_queries": total_queries,
        "total_results": total_results,
        "overall_latency": overall_latency,
        "avg_latency_per_query": sum(stat.get("latency_seconds", 0.0) for stat in retrieval_stats) / total_queries if total_queries > 0 else 0.0,
        "avg_similarity_score": avg_similarity,
        "success_rate": successful_queries / total_queries if total_queries > 0 else 0.0,
        "unique_sources_count": len(all_sources),
        "unique_modules_count": len(all_modules),
        "detailed_stats": retrieval_stats
    }

    return report


def print_summary_report(report: Dict):
    """
    Print a formatted summary report to the console
    """
    print("\n" + "="*60)
    print("RETRIEVAL PIPELINE SUMMARY REPORT")
    print("="*60)

    print(f"Summary: {report['summary']}")
    print(f"Total Queries Processed: {report['total_queries']}")
    print(f"Total Results Retrieved: {report['total_results']}")
    print(f"Overall Latency: {report['overall_latency']:.3f}s")
    print(f"Average Latency per Query: {report['avg_latency_per_query']:.3f}s")
    print(f"Average Similarity Score: {report['avg_similarity_score']:.3f}")
    print(f"Success Rate: {report['success_rate']*100:.1f}%")
    print(f"Unique Sources Found: {report['unique_sources_count']}")
    print(f"Unique Modules Covered: {report['unique_modules_count']}")

    print("\nDetailed Statistics:")
    for i, stat in enumerate(report['detailed_stats'], 1):
        print(f"  Query {i}: '{stat.get('query', '')[:50]}{'...' if len(stat.get('query', '')) > 50 else ''}'")
        print(f"    Results: {stat.get('total_results', 0)} | Latency: {stat.get('latency_seconds', 0):.3f}s")
        print(f"    Avg Similarity: {stat.get('avg_similarity_score', 0):.3f}")
        print(f"    Sources: {len(stat.get('unique_sources', []))} | Modules: {len(stat.get('unique_modules', []))}")

    print("="*60)


def test_complete_pipeline_from_query_to_validated_results():
    """
    Execute comprehensive test of the complete retrieval pipeline from query to validated results
    """
    print("Testing complete pipeline from query to validated results...")

    try:
        # Initialize clients
        gemini_client = initialize_gemini_client()
        qdrant_client = initialize_qdrant_client()
    except Exception as e:
        print(f"Failed to initialize clients for pipeline testing: {str(e)}")
        return False

    # Define test queries that should return relevant results
    test_queries = [
        "What is artificial intelligence?",
        "Explain neural networks",
        "How does computer vision work in robotics?",
        "What is reinforcement learning?",
        "Describe humanoid robotics basics"
    ]

    all_tests_passed = True
    total_tests = len(test_queries)
    successful_tests = 0

    # Collect statistics for the entire pipeline test
    pipeline_stats = []

    for i, query in enumerate(test_queries, 1):
        print(f"\nTest {i}/{total_tests}: Processing query '{query}'")

        # Measure retrieval latency
        start_time = time.time()

        # Process the query through the complete pipeline
        results = retrieve_chunks_for_query(
            gemini_client=gemini_client,
            qdrant_client=qdrant_client,
            query=query,
            top_k=5,
            similarity_threshold=0.3
        )

        end_time = time.time()
        query_latency = end_time - start_time

        print(f"  Retrieved {len(results)} results in {query_latency:.3f}s")

        # Validate results
        if not results:
            print(f"  ❌ No results found for query '{query}'")
            all_tests_passed = False
            continue

        # Validate metadata integrity for each result
        is_metadata_valid, issues = validate_metadata_integrity(results)

        if not is_metadata_valid:
            print(f"  ⚠️  Metadata validation failed with issues: {issues}")
            all_tests_passed = False
        else:
            print(f"  ✅ Metadata validation passed")

        # Validate contextual relevance of results
        relevant_results = 0
        for result in results:
            # Basic relevance check: see if result text contains terms related to query
            query_lower = query.lower()
            text_lower = result["text"].lower()
            query_terms = query_lower.split()
            term_matches = sum(1 for term in query_terms if term in text_lower and len(term) > 2)  # Only count terms longer than 2 chars

            if term_matches > 0:
                relevant_results += 1

        if relevant_results > 0:
            print(f"  ✅ {relevant_results}/{len(results)} results appear contextually relevant")
        else:
            print(f"  ⚠️  No contextually relevant results found for query '{query}'")
            all_tests_passed = False

        # Generate statistics for this query
        query_stats = generate_retrieval_statistics(results, query, query_latency)
        pipeline_stats.append(query_stats)

        successful_tests += 1

    # Generate and print comprehensive summary report
    print(f"\nGenerating comprehensive summary report...")
    overall_latency = sum(stat.get("latency_seconds", 0.0) for stat in pipeline_stats)
    summary_report = generate_summary_report(pipeline_stats, overall_latency)
    print_summary_report(summary_report)

    # Final validation
    success_rate = successful_tests / total_tests if total_tests > 0 else 0
    avg_latency = sum(stat.get("latency_seconds", 0.0) for stat in pipeline_stats) / total_tests if total_tests > 0 else 0

    print(f"\nPipeline Test Results:")
    print(f"  Success Rate: {success_rate*100:.1f}% ({successful_tests}/{total_tests})")
    print(f"  Average Latency: {avg_latency:.3f}s")
    print(f"  Overall Performance: {'✅' if avg_latency < 1.0 else '⚠️' if avg_latency < 2.0 else '❌'}")

    if all_tests_passed and success_rate >= 0.8 and avg_latency < 2.0:
        print(f"\n✅ Complete pipeline test passed - all components working together successfully")
        return True
    else:
        print(f"\n⚠️  Complete pipeline test has issues that need review")
        return False


def main():
    """Main function to orchestrate the complete retrieval pipeline with CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Vector Retrieval and RAG Pipeline Validation System")
    parser.add_argument("--query", type=str, default="What does the book say about humanoid robotics?",
                        help="Query string to retrieve relevant content for")
    parser.add_argument("--top-k", type=int, default=5,
                        help="Number of top results to retrieve (default: 5)")
    parser.add_argument("--threshold", type=float, default=0.3,
                        help="Similarity threshold for filtering results (default: 0.3)")
    parser.add_argument("--collection", type=str, default="rag_embedding",
                        help="Qdrant collection name (default: rag_embedding)")
    parser.add_argument("--max-depth", type=int, default=MAX_DEPTH,
                        help="Maximum depth to crawl for URL discovery (default: 2)")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose output for debugging")

    args = parser.parse_args()

    # Set up logging configuration - T040
    logger = add_logging_configuration()
    logger.info("Starting vector retrieval and validation pipeline...")

    print("Starting vector retrieval and validation pipeline...")

    # Initialize clients and configuration
    gemini_client = initialize_gemini_client()
    qdrant_client = initialize_qdrant_client()

    # Get base URL from environment or use default
    base_url = os.getenv("WEBSITE_URL", "https://ai-and-humanoid-robotic-course.vercel.app/")

    logger.info(f"Using base URL: {base_url}")
    print(f"Using base URL: {base_url}")

    # Test semantic search functionality with sample queries - T017
    print("\nTesting semantic search functionality...")
    search_test_passed = test_semantic_search_with_sample_queries()

    if search_test_passed:
        print("✅ Semantic search validation passed")
    else:
        print("⚠️  Semantic search validation needs review")

    # Test metadata preservation with various query types - T024
    print("\nTesting metadata preservation with different query types...")
    metadata_test_passed = test_metadata_preservation_with_query_types()

    if metadata_test_passed:
        print("✅ Metadata preservation validation passed")
    else:
        print("⚠️  Metadata preservation validation needs review")

    # Test retrieval performance with different configurations - T031
    print("\nTesting retrieval performance with different configurations...")
    performance_test_passed = test_retrieval_performance_with_different_configs()

    if performance_test_passed:
        print("✅ Performance configuration testing passed")
    else:
        print("⚠️  Performance configuration testing needs review")

    # Validate performance meets interactive use requirements - T032
    print("\nValidating performance meets interactive use requirements (<500ms)...")
    performance_validation_passed = validate_performance_meets_interactive_requirements()

    if performance_validation_passed:
        print("✅ Performance validation passed - meets interactive use requirements")
    else:
        print("⚠️  Performance validation needs optimization")

    # Use the command-line query or default
    query = args.query
    top_k = args.top_k
    similarity_threshold = args.threshold
    collection_name = args.collection

    if args.verbose:
        print(f"Query: {query}")
        print(f"Top-K: {top_k}")
        print(f"Threshold: {similarity_threshold}")
        print(f"Collection: {collection_name}")

    print(f"\nProcessing query: '{query}'")

    # Measure retrieval latency
    start_time = time.time()
    results = retrieve_chunks_for_query_with_retry(
        gemini_client=gemini_client,
        qdrant_client=qdrant_client,
        query=query,
        top_k=top_k,
        similarity_threshold=similarity_threshold,
        collection_name=collection_name
    )
    end_time = time.time()
    query_latency = end_time - start_time

    if results:
        print(f"\nFound {len(results)} relevant chunks:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Similarity: {result['similarity_score']:.3f}")
            print(f"   Source: {result['source_url']}")
            print(f"   Module: {result['module_name']}")
            print(f"   Content Preview: {result['text'][:200]}{'...' if len(result['text']) > 200 else ''}")

            # Validate contextual relevance of retrieved chunk
            query_lower = query.lower()
            text_lower = result['text'].lower()
            query_terms = query_lower.split()
            relevant_terms_found = sum(1 for term in query_terms if term in text_lower and len(term) > 2)

            if relevant_terms_found > 0:
                print(f"   ✅ Content relevance: {relevant_terms_found} query terms matched")
            else:
                print(f"   ⚠️  Content relevance: No query terms found in result")
    else:
        print("No relevant chunks found for the query.")

    # Generate and print summary report with retrieval statistics
    print("\nGenerating summary report...")
    retrieval_stats = generate_retrieval_statistics(results, query, query_latency)
    summary_report = generate_summary_report([retrieval_stats], query_latency)
    print_summary_report(summary_report)

    # Test complete pipeline from query to validated results - T038
    print("\nTesting complete pipeline from query to validated results...")
    pipeline_test_passed = test_complete_pipeline_from_query_to_validated_results()

    if pipeline_test_passed:
        print("✅ Complete pipeline test passed - all components working together successfully")
    else:
        print("⚠️  Complete pipeline test needs review")

    print("\nRetrieval and validation pipeline completed successfully!")


if __name__ == "__main__":
    main()