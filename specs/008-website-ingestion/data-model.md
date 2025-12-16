# Data Model: Website URL Ingestion, Embedding Generation, and Vector Storage

## Content Chunk
- **Fields**:
  - text: string (the extracted and cleaned content)
  - source_url: string (URL where the content was found)
  - module_name: string (name of the module/chapter the content belongs to)
  - chunk_index: integer (position of this chunk within the document)
  - created_at: timestamp (when the chunk was created)
- **Validation**: Text must not be empty, source_url must be a valid URL
- **Relationships**: One-to-many with Embedding Vector (one chunk generates one vector)

## Embedding Vector
- **Fields**:
  - vector: array of floats (numerical representation of content chunk)
  - chunk_id: string (identifier linking to the source content chunk)
  - dimensions: integer (size of the embedding vector)
- **Validation**: Vector must have consistent dimensions as defined by the Cohere model
- **Relationships**: One-to-one with Content Chunk (each chunk has one vector representation)

## Vector Record (Qdrant Point)
- **Fields**:
  - id: string (unique identifier for the vector in Qdrant)
  - vector: array of floats (the embedding vector)
  - payload: object containing metadata
    - text: string (the original text chunk)
    - source_url: string (URL where the content was found)
    - module_name: string (name of the module/chapter)
    - chunk_index: integer (position of this chunk within the document)
- **Validation**: All required metadata fields must be present
- **Relationships**: Maps to both Content Chunk and Embedding Vector

## Crawling Job
- **Fields**:
  - id: string (unique identifier for the crawling job)
  - start_urls: array of strings (list of URLs to begin crawling from)
  - discovered_urls: array of strings (list of URLs found during crawling)
  - processed_urls: array of strings (list of URLs successfully processed)
  - status: string (current state: 'pending', 'in_progress', 'completed', 'failed')
  - created_at: timestamp (when the job was created)
  - completed_at: timestamp (when the job was completed, if applicable)
- **Validation**: Must have at least one start URL
- **State transitions**: pending → in_progress → completed/failed