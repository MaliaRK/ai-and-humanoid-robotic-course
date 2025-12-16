# API Contracts: Vector Retrieval and RAG Pipeline Validation

## Function: retrieve_similar_chunks
- **Purpose**: Retrieve semantically similar content chunks from Qdrant based on a query
- **Input**:
  - query_text: string (the search query text)
  - top_k: integer (optional, default 5, number of results to return)
  - similarity_threshold: float (optional, default 0.5, minimum similarity score for inclusion)
  - filters: dict (optional, metadata filters to apply to the search)
- **Output**:
  - List of objects with fields:
    - text: string (the retrieved content chunk)
    - similarity_score: float (cosine similarity score between query and chunk)
    - metadata: object containing
      - source_url: string (URL where the content was found)
      - module_name: string (name of the module/chapter)
      - chunk_index: integer (position of this chunk in the original document)
- **Error handling**: Raises exceptions for invalid parameters or connection issues
- **Side effects**: Makes semantic search request to Qdrant

## Function: validate_retrieval_quality
- **Purpose**: Validate that retrieved chunks are contextually relevant to the query
- **Input**:
  - query_text: string (the original query)
  - retrieved_chunks: List[objects] (chunks returned by retrieval function)
  - expected_topic: string (optional, expected subject matter for validation)
- **Output**:
  - Object with fields:
    - is_relevant: boolean (whether chunks are relevant to query)
    - relevance_score: float (0.0-1.0 score of overall relevance)
    - validation_details: List[string] (descriptions of validation results)
- **Error handling**: Returns validation results even if some internal checks fail
- **Side effects**: None (pure validation function)

## Function: measure_retrieval_performance
- **Purpose**: Measure and report performance metrics for retrieval operations
- **Input**:
  - query_text: string (the query to measure performance for)
  - top_k: integer (number of results to retrieve)
- **Output**:
  - Object with fields:
    - query_latency: float (time in seconds to complete retrieval)
    - result_count: integer (number of chunks returned)
    - average_chunk_size: float (average size of returned chunks in characters)
    - confidence_metrics: object containing
      - min_similarity: float (lowest similarity score among results)
      - max_similarity: float (highest similarity score among results)
      - avg_similarity: float (average similarity score)
- **Error handling**: Reports error as part of metrics if retrieval fails
- **Side effects**: Performs retrieval operation and measures timing

## Function: configure_retrieval_parameters
- **Purpose**: Set configuration parameters for the retrieval system
- **Input**:
  - top_k_default: integer (default number of results to return)
  - similarity_threshold: float (default minimum similarity for inclusion)
  - batch_size: integer (default batch size for processing multiple queries)
- **Output**:
  - boolean (true if configuration was successfully applied)
- **Error handling**: Raises exception for invalid parameter values
- **Side effects**: Updates global configuration for retrieval operations

## Function: test_retrieval_pipeline
- **Purpose**: Execute comprehensive test of the retrieval pipeline with predefined queries
- **Input**:
  - test_queries: List[string] (queries to use for testing)
  - expected_results: List[objects] (expected content or topics for validation)
- **Output**:
  - Object with fields:
    - success_rate: float (fraction of queries that returned relevant results)
    - average_latency: float (mean retrieval time across all queries)
    - validation_summary: string (summary of test results)
    - detailed_results: List[objects] with fields
      - query: string (the test query)
      - success: boolean (whether the query returned relevant results)
      - latency: float (time taken for this query)
      - relevance_score: float (relevance of results)
- **Error handling**: Continues testing other queries even if individual queries fail
- **Side effects**: Performs multiple retrieval operations for testing purposes