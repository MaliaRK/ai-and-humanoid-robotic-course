import os
from typing import Optional
import google.generativeai as genai
from .config import validate_environment

# Validate environment before initializing client
is_valid, missing_vars = validate_environment()
if not is_valid:
    raise EnvironmentError(f"Missing required environment variables: {missing_vars}")

# Initialize Google Gemini client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

genai.configure(api_key=GEMINI_API_KEY)

# Get the generative model
model = genai.GenerativeModel('gemini-2.5-flash')

def get_gemini_model():
    """
    Get the initialized Gemini model.

    Returns:
        GenerativeModel: The Gemini model instance
    """
    return model