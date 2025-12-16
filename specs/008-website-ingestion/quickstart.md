# Quickstart Guide: Website Ingestion System

## Prerequisites
- Python 3.10+
- UV package manager
- Cohere API key
- Qdrant Cloud account and API key

## Setup

1. **Create the backend directory:**
```bash
mkdir backend
cd backend
```

2. **Initialize the project with UV:**
```bash
uv init
```

3. **Create requirements.txt:**
```txt
cohere==5.5.3
qdrant-client==1.9.1
requests==2.31.0
beautifulsoup4==4.12.2
numpy==1.24.3
```

4. **Install dependencies:**
```bash
uv pip install -r requirements.txt
```

5. **Create .env file with your credentials:**
```env
COHERE_API_KEY=your_cohere_api_key_here
QDRANT_URL=your_qdrant_cloud_url_here
QDRANT_API_KEY=your_qdrant_api_key_here
```

## Usage

1. **Run the ingestion script:**
```bash
python main.py
```

The script will:
- Discover all URLs on the target website
- Extract clean text from each page
- Chunk the content appropriately
- Generate embeddings using Cohere
- Store vectors with metadata in Qdrant Cloud

## Configuration

The system uses environment variables for configuration:
- `COHERE_API_KEY`: Your Cohere API key
- `QDRANT_URL`: Your Qdrant Cloud endpoint
- `QDRANT_API_KEY`: Your Qdrant API key
- `WEBSITE_URL`: Base URL to crawl (default: https://ai-and-humanoid-robotic-course.vercel.app/)

## Output

The system will create a Qdrant collection named `rag_embedding` containing:
- Embedding vectors for each content chunk
- Metadata including source URL, module name, and chunk index
- Original text content for retrieval