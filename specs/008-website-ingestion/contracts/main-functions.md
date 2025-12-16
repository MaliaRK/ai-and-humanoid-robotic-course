# API Contracts: Main Functions for Website Ingestion System

## Function: get_all_urls
- **Purpose**: Discover all URLs on the target website starting from the base URL
- **Input**:
  - base_url: string (the starting URL to crawl, e.g., "https://ai-and-humanoid-robotic-course.vercel.app/")
  - max_depth: integer (optional, default 2, maximum depth to crawl)
- **Output**:
  - Array of strings (list of discovered URLs)
- **Error handling**: Returns empty array if base URL is unreachable
- **Side effects**: None

## Function: extract_text_from_url
- **Purpose**: Extract clean text content from a given URL
- **Input**:
  - url: string (the URL to extract content from)
- **Output**:
  - Object with fields:
    - text: string (clean text content extracted from the page)
    - module_name: string (name of the module/chapter derived from URL structure)
- **Error handling**: Throws exception if URL is unreachable or content extraction fails
- **Side effects**: Makes HTTP request to the provided URL

## Function: chunk_text
- **Purpose**: Split text content into semantic chunks of appropriate size
- **Input**:
  - text: string (the text content to chunk)
  - chunk_size: integer (optional, default 512, maximum size of each chunk in tokens/characters)
  - overlap: integer (optional, default 50, overlap between chunks to maintain context)
- **Output**:
  - Array of strings (list of text chunks)
- **Error handling**: Returns empty array if input text is empty
- **Side effects**: None

## Function: embed
- **Purpose**: Generate semantic embeddings for text chunks using Cohere
- **Input**:
  - text_chunks: array of strings (the text chunks to embed)
- **Output**:
  - Array of embedding vectors (arrays of floats)
- **Error handling**: Throws exception if Cohere API call fails or rate limit exceeded
- **Side effects**: Makes API call to Cohere service

## Function: create_collection
- **Purpose**: Create a Qdrant collection for storing embeddings
- **Input**:
  - collection_name: string (name of the collection, default "rag_embedding")
  - vector_size: integer (dimension of the embedding vectors)
  - distance_function: string (optional, default "Cosine", distance function for similarity search)
- **Output**:
  - Boolean (true if collection created successfully, false if already exists)
- **Error handling**: Throws exception if Qdrant connection fails
- **Side effects**: Creates collection in Qdrant Cloud

## Function: save_chunk_to_qdrant
- **Purpose**: Save a text chunk with its embedding and metadata to Qdrant
- **Input**:
  - text_chunk: string (the original text chunk)
  - embedding: array of floats (the embedding vector)
  - metadata: object with fields:
    - source_url: string (URL where the content was found)
    - module_name: string (name of the module/chapter)
    - chunk_index: integer (position of this chunk within the document)
  - collection_name: string (name of the collection to store in)
- **Output**:
  - Point ID: string (the ID assigned to the stored vector in Qdrant)
- **Error handling**: Throws exception if Qdrant storage fails
- **Side effects**: Stores data in Qdrant Cloud

## Function: main
- **Purpose**: Execute the complete ingestion pipeline
- **Input**:
  - base_url: string (optional, default "https://ai-and-humanoid-robotic-course.vercel.app/", the starting URL to process)
- **Output**:
  - Object with fields:
    - status: string ("completed" or "failed")
    - processed_urls: integer (count of URLs processed)
    - stored_chunks: integer (count of chunks stored in Qdrant)
    - execution_time: float (time taken in seconds)
- **Error handling**: Logs errors and continues processing when possible
- **Side effects**:
  - Crawls the website
  - Makes Cohere API calls
  - Stores data in Qdrant Cloud
  - May exceed free-tier limits if not properly managed