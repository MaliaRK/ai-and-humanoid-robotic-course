import os
from typing import Optional
from openai import OpenAI
from .config import validate_environment

# Validate environment before initializing client
is_valid, missing_vars = validate_environment()
if not is_valid:
    raise EnvironmentError(f"Missing required environment variables: {missing_vars}")

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

client = OpenAI(api_key=OPENAI_API_KEY)

def get_openai_client() -> OpenAI:
    """
    Get the initialized OpenAI client.

    Returns:
        OpenAI: The OpenAI client instance
    """
    return client