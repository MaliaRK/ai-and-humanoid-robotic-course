# Data Model: Vector Retrieval and RAG Pipeline

## Query Embedding
- **Attributes**:
  - vector: List[float] (numerical representation of the search query)
  - text: string (original query text)
  - created_at: datetime (timestamp of when the embedding was generated)
- **Validation**: Vector must have consistent dimensions (1024 for Cohere embed-english-v3.0)
- **Relationships**: One-to-many with Retrieved Chunks (one query can match multiple chunks)

## Retrieved Chunk
- **Attributes**:
  - text: string (content of the retrieved text chunk)
  - embedding: List[float] (vector representation of the content)
  - similarity_score: float (cosine similarity score relative to the query)
  - position: integer (position of this chunk in the original document)
- **Validation**: Text must not be empty, similarity score between 0 and 1
- **Relationships**: Many-to-one with Query Embedding (many chunks can match one query)

## Metadata Package
- **Attributes**:
  - source_url: string (URL where the content was originally found)
  - module_name: string (name of the book module/chapter the content belongs to)
  - chunk_index: integer (position of this chunk within the document)
  - retrieval_timestamp: datetime (when this chunk was retrieved)
- **Validation**: All fields must be non-empty, chunk_index must be non-negative
- **Relationships**: One-to-one with Retrieved Chunk (each chunk has one metadata package)

## Search Configuration
- **Attributes**:
  - top_k: integer (number of results to return)
  - similarity_threshold: float (minimum similarity score for inclusion)
  - search_algorithm: string (cosine similarity, dot product, etc.)
  - filters: Dict (optional filters to apply to the search)
- **Validation**: top_k must be positive, similarity_threshold between 0 and 1
- **Relationships**: One-to-many with Query Embedding (one configuration can be used for multiple queries)

## Retrieval Result
- **Attributes**:
  - query_embedding: Query Embedding (reference to the query that generated this result)
  - chunks: List[Retrieved Chunk] (list of content chunks returned)
  - metadata_packages: List[Metadata Package] (metadata for each chunk)
  - retrieval_latency: float (time taken to perform the retrieval in milliseconds)
  - total_chunks_found: integer (total number of matching chunks found before top-k filtering)
- **Validation**: Must have same number of chunks and metadata packages, latency must be positive
- **Relationships**: Composed of Query Embedding, Retrieved Chunks, and Metadata Packages