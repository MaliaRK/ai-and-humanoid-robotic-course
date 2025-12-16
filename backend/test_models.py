#!/usr/bin/env python3
"""
Test script to check available Gemini models
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="./.env")

# Initialize Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

genai.configure(api_key=GEMINI_API_KEY)

try:
    # List available models
    print("Available models:")
    for model in genai.list_models():
        print(f"  - {model.name}")
        print(f"    - Description: {model.description}")
        print(f"    - Supported generation methods: {model.supported_generation_methods}")
        print()

    # Try to initialize a known working model
    print("Testing gemini-1.0-pro model...")
    model = genai.GenerativeModel('gemini-1.0-pro')
    print("gemini-1.0-pro initialized successfully")

except Exception as e:
    print(f"Error: {e}")