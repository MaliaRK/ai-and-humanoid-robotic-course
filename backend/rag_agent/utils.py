import time
import logging
import uuid
from typing import Callable, Any, Optional
from functools import wraps
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError
import openai
from openai import RateLimitError, APIConnectionError, APIError
import google.generativeai as genai
from google.generativeai.types import BlockedPromptException
from qdrant_client.http.exceptions import UnexpectedResponse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_conversation_id() -> str:
    """
    Generate a unique conversation ID.

    Returns:
        str: A UUID string for the conversation
    """
    return str(uuid.uuid4())

def generate_query_id() -> str:
    """
    Generate a unique query ID.

    Returns:
        str: A UUID string for the query
    """
    return str(uuid.uuid4())

def generate_response_id() -> str:
    """
    Generate a unique response ID.

    Returns:
        str: A UUID string for the response
    """
    return str(uuid.uuid4())

def generate_chunk_id() -> str:
    """
    Generate a unique chunk ID.

    Returns:
        str: A UUID string for the chunk
    """
    return str(uuid.uuid4())

def handle_rate_limit_error(error: Exception) -> bool:
    """
    Check if the error is a rate limit error and handle it appropriately.

    Args:
        error: The exception to check

    Returns:
        bool: True if it's a rate limit error, False otherwise
    """
    if isinstance(error, (RateLimitError,)):
        logger.warning(f"Rate limit error occurred: {error}")
        return True
    elif "rate" in str(error).lower() and "limit" in str(error).lower():
        logger.warning(f"Rate limit error detected from message: {error}")
        return True
    elif "quota" in str(error).lower():
        logger.warning(f"Quota error detected: {error}")
        return True
    return False

def handle_network_error(error: Exception) -> bool:
    """
    Check if the error is a network error and handle it appropriately.

    Args:
        error: The exception to check

    Returns:
        bool: True if it's a network error, False otherwise
    """
    if isinstance(error, (APIConnectionError, ConnectionError, requests.ConnectionError)):
        logger.warning(f"Network error occurred: {error}")
        return True
    elif isinstance(error, Timeout):
        logger.warning(f"Timeout error occurred: {error}")
        return True
    elif "connection" in str(error).lower() or "timeout" in str(error).lower():
        logger.warning(f"Network-related error detected: {error}")
        return True
    return False

def handle_content_filter_error(error: Exception) -> bool:
    """
    Check if the error is a content filtering error.

    Args:
        error: The exception to check

    Returns:
        bool: True if it's a content filter error, False otherwise
    """
    if isinstance(error, (BlockedPromptException,)):
        logger.warning(f"Content filter error occurred: {error}")
        return True
    elif "content" in str(error).lower() and "policy" in str(error).lower():
        logger.warning(f"Content policy error detected: {error}")
        return True
    return False

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0
):
    """
    Decorator to retry a function with exponential backoff for specific errors.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        backoff_factor: Factor by which delay increases after each retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # Check if this is an error we should retry for
                    if (handle_rate_limit_error(e) or
                        handle_network_error(e) or
                        isinstance(e, (UnexpectedResponse,))):

                        if attempt < max_retries:
                            delay = base_delay * (backoff_factor ** attempt)
                            logger.info(f"Attempt {attempt + 1} failed with {type(e).__name__}: {e}. Retrying in {delay}s...")
                            time.sleep(delay)
                        else:
                            logger.error(f"Max retries ({max_retries}) exceeded after {attempt + 1} attempts")
                    else:
                        # If it's not a retryable error, raise immediately
                        logger.error(f"Non-retryable error occurred: {type(e).__name__}: {e}")
                        raise e

            # If we exhausted all retries, raise the last exception
            raise last_exception
        return wrapper
    return decorator

def format_error_response(error: Exception) -> dict:
    """
    Format an error response for API return.

    Args:
        error: The exception to format

    Returns:
        dict: Formatted error response
    """
    error_type = type(error).__name__

    if handle_rate_limit_error(error):
        return {
            "error": "RATE_LIMIT_EXCEEDED",
            "message": "Rate limit exceeded, please try again later",
            "code": "RATE_LIMIT_EXCEEDED"
        }
    elif handle_content_filter_error(error):
        return {
            "error": "CONTENT_FILTERED",
            "message": "Content was filtered due to safety policies",
            "code": "CONTENT_FILTERED"
        }
    elif handle_network_error(error):
        return {
            "error": "SERVICE_UNAVAILABLE",
            "message": f"Service temporarily unavailable: {str(error)}",
            "code": "SERVICE_UNAVAILABLE"
        }
    else:
        return {
            "error": "INTERNAL_ERROR",
            "message": f"An internal error occurred: {str(error)}",
            "code": "INTERNAL_ERROR"
        }

def validate_response_content(response: str) -> tuple[bool, Optional[str]]:
    """
    Validate that the response content is appropriate.

    Args:
        response: The response content to validate

    Returns:
        tuple: (is_valid, error_message if invalid)
    """
    if not response or not response.strip():
        return False, "Response is empty or contains only whitespace"

    if len(response) > 10000:  # Arbitrary limit, can be adjusted
        return False, "Response exceeds maximum length"

    return True, None