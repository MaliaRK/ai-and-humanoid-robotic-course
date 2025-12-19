import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Application Configuration
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "ai_book_embedding")
AGENT_MODEL = os.getenv("AGENT_MODEL", "gpt-4")
AGENT_TEMPERATURE = float(os.getenv("AGENT_TEMPERATURE", "0.7"))
MAX_RETRIEVAL_CHUNKS = int(os.getenv("MAX_RETRIEVAL_CHUNKS", "5"))
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "5"))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.3"))

# Validation function to check required environment variables
def validate_environment() -> tuple[bool, list[str]]:
    """
    Validate that all required environment variables are set.

    Returns:
        tuple: (is_valid, list of missing environment variables)
    """
    required_vars = [
        "GEMINI_API_KEY",
        "QDRANT_URL",
        "QDRANT_API_KEY",
        "NEON_DATABASE_URL"
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    return len(missing_vars) == 0, missing_vars