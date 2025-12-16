import os
from typing import Optional
from qdrant_client import QdrantClient
from rag_agent.config import validate_environment

# Validate environment before initializing client
is_valid, missing_vars = validate_environment()
if not is_valid:
    raise EnvironmentError(f"Missing required environment variables: {missing_vars}")

# Initialize Qdrant client
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

if not QDRANT_URL or not QDRANT_API_KEY:
    raise ValueError("QDRANT_URL and QDRANT_API_KEY environment variables are required")

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)

def get_qdrant_client():
    """
    Get the initialized Qdrant client.

    Returns:
        QdrantClient: The Qdrant client instance
    """
    return client