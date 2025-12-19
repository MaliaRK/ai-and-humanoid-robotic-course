import os
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.models import PointStruct
import logging
from urllib.parse import urljoin, urlparse
import time
import uuid
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load environment variables from the project root
import sys
from pathlib import Path
# Add the project root to the path so we can load .env from there
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(dotenv_path=project_root / ".env")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocusaurusEmbeddingPipeline:
    def __init__(self):
        # Initialize sentence transformer model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight model for local embeddings

        # Local model returns 384-dimensional vectors
        self.vector_size = 384

        # Initialize Qdrant client
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")

        if qdrant_api_key:
            self.qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        else:
            self.qdrant_client = QdrantClient(url=qdrant_url)

        # Target URL for the Docusaurus site
        self.target_url = "https://ai-and-humanoid-robotic-course.vercel.app/"

    def get_all_urls(self, base_url: str) -> List[str]:
        """
        Extract all URLs from a deployed Docusaurus site using sitemap
        """
        urls = []

        try:
            # Try to get URLs from sitemap first
            sitemap_url = urljoin(base_url, "sitemap.xml")
            response = requests.get(sitemap_url)

            if response.status_code == 200:
                root = ET.fromstring(response.content)

                # Handle both sitemap index and regular sitemap
                if root.tag.endswith('sitemapindex'):
                    # If it's a sitemap index, get individual sitemaps
                    for sitemap in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
                        sitemap_response = requests.get(sitemap.text)
                        if sitemap_response.status_code == 200:
                            sitemap_root = ET.fromstring(sitemap_response.content)
                            for url_elem in sitemap_root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
                                # Replace placeholder domain with actual domain
                                url = url_elem.text.replace("https://your-docusaurus-site.example.com", "https://ai-and-humanoid-robotic-course.vercel.app")
                                urls.append(url)
                else:
                    # Regular sitemap
                    for url_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
                        # Replace placeholder domain with actual domain
                        url = url_elem.text.replace("https://your-docusaurus-site.example.com", "https://ai-and-humanoid-robotic-course.vercel.app")
                        urls.append(url)
            else:
                # Fallback: try to crawl the site by looking for links
                logger.info(f"Sitemap not found at {sitemap_url}, attempting to crawl...")

                # Get the main page and extract links
                response = requests.get(base_url)
                soup = BeautifulSoup(response.content, 'html.parser')

                # Find all links within the page
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(base_url, href)

                    # Only add URLs from the same domain
                    if urlparse(full_url).netloc == urlparse(base_url).netloc:
                        if full_url not in urls and full_url.startswith(base_url):
                            urls.append(full_url)

        except Exception as e:
            logger.error(f"Error getting URLs from {base_url}: {e}")

        return urls

    def extract_text_from_url(self, url: str) -> str:
        """
        Extract and clean text from a single URL
        """
        try:
            response = requests.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Look for main content containers typically used in Docusaurus
            # Try multiple selectors to find the main content
            content_selectors = [
                'article',  # Main article content
                '.markdown',  # Docusaurus markdown content
                '.theme-doc-markdown',  # Docusaurus theme markdown
                '.main-wrapper',  # Main content wrapper
                'main',  # Main content area
                '.container',  # Container with content
                '[role="main"]'  # Main role
            ]

            content = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    for element in elements:
                        # Get text but try to preserve some structure
                        text = element.get_text(separator=' ', strip=True)
                        if len(text) > len(content):
                            content = text
                    break

            # If no specific content found, get all body text
            if not content:
                body = soup.find('body')
                if body:
                    content = body.get_text(separator=' ', strip=True)

            # Clean up the text
            lines = (line.strip() for line in content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            content = ' '.join(chunk for chunk in chunks if chunk)

            return content

        except Exception as e:
            logger.error(f"Error extracting text from {url}: {e}")
            return ""

    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """
        Split text into chunks with overlap to preserve context
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)

            # Move start position by chunk_size - overlap
            start = end - overlap

            # If remaining text is less than chunk_size, add it as final chunk
            if len(text) - start < chunk_size:
                if start < len(text):
                    final_chunk = text[start:]
                    if final_chunk not in chunks:  # Avoid duplicate chunks
                        chunks.append(final_chunk)
                break

        return chunks

    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for text using local sentence transformer model
        """
        try:
            # Generate embedding using local model
            embedding = self.model.encode([text])[0].tolist()
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding for text: {e}")
            return []

    def create_collection(self, collection_name: str = "ai_book_embedding"):
        """
        Create a Qdrant collection for storing embeddings
        """
        try:
            # Check if collection already exists
            collections = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if collection_name in collection_names:
                logger.info(f"Collection {collection_name} already exists")
                return

            # Create collection with appropriate vector size (384 for sentence transformer embeddings)
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
            )

            logger.info(f"Created collection {collection_name} with 384-dimension vectors")

        except Exception as e:
            logger.error(f"Error creating collection {collection_name}: {e}")
            raise

    def save_chunk_to_qdrant(self, content: str, url: str, embedding: List[float], position: int, collection_name: str = "ai_book_embedding"):
        """
        Save a text chunk with its embedding to Qdrant
        """
        try:
            # Generate a unique ID for the point
            point_id = str(uuid.uuid4())

            # Prepare the payload with metadata
            payload = {
                "content": content,
                "source_url": url,
                "chunk_index": position,
                "created_at": time.time()
            }

            # Create and upload the point to Qdrant
            points = [PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            )]

            self.qdrant_client.upsert(
                collection_name=collection_name,
                points=points
            )

            logger.info(f"Saved chunk to Qdrant: {url} (position {position})")
            return True

        except Exception as e:
            logger.error(f"Error saving chunk to Qdrant: {e}")
            return False

def main():
    """
    Main function to execute the complete pipeline
    """
    logger.info("Starting Docusaurus Embedding Pipeline...")

    # Initialize the pipeline
    pipeline = DocusaurusEmbeddingPipeline()

    try:
        # Step 1: Create the Qdrant collection
        logger.info("Creating Qdrant collection...")
        pipeline.create_collection("ai_book_embedding")

        # Step 2: Get all URLs from the target Docusaurus site
        logger.info(f"Extracting URLs from {pipeline.target_url}...")
        urls = pipeline.get_all_urls(pipeline.target_url)

        if not urls:
            logger.warning(f"No URLs found at {pipeline.target_url}")
            return

        # Filter to only include module 1, 2, 3, and 4 documents for today's submission
        module_urls = [url for url in urls if any(f"/module-{i}" in url.lower() for i in range(1, 5))]
        urls = module_urls
        logger.info(f"Filtered to {len(urls)} URLs for modules 1, 2, 3, and 4 for today's submission")

        # Step 3: Process each URL
        total_chunks = 0
        for i, url in enumerate(urls):
            logger.info(f"Processing URL {i+1}/{len(urls)}: {url}")

            # Extract text from the URL
            text_content = pipeline.extract_text_from_url(url)

            if not text_content:
                logger.warning(f"No content extracted from {url}")
                continue

            logger.info(f"Extracted {len(text_content)} characters from {url}")

            # Chunk the text
            chunks = pipeline.chunk_text(text_content)
            logger.info(f"Created {len(chunks)} chunks from {url}")

            # Process each chunk
            for j, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue

                # Generate embedding
                embedding = pipeline.embed(chunk)

                if not embedding:
                    logger.error(f"Failed to generate embedding for chunk {j} of {url}")
                    continue

                # Save to Qdrant
                success = pipeline.save_chunk_to_qdrant(
                    content=chunk,
                    url=url,
                    embedding=embedding,
                    position=j
                )

                if success:
                    total_chunks += 1
                    logger.info(f"Successfully saved chunk {j} of {url} to Qdrant")
                    # Add longer delay to stay within free tier rate limits
                    time.sleep(60)  # 60 seconds delay between chunks to stay within free tier limits
                else:
                    logger.error(f"Failed to save chunk {j} of {url} to Qdrant")

        logger.info(f"Pipeline completed successfully! Total chunks saved: {total_chunks}")

    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        raise

if __name__ == "__main__":
    main()