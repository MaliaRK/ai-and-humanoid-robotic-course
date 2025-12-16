# Quickstart: Frontend and Backend Integration for RAG Chatbot

## Overview
This guide provides instructions for setting up and running the integrated RAG chatbot in the Docusaurus documentation site.

## Prerequisites
- Node.js 16+ for Docusaurus frontend
- Python 3.10+ for FastAPI backend
- Access to required API keys (OpenAI, Google Gemini, Qdrant)
- Running FastAPI RAG backend service

## Backend Setup
1. Ensure the FastAPI RAG backend is running:
   ```bash
   cd backend
   python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
   ```

2. Verify the backend is accessible:
   ```bash
   curl http://localhost:8000/health
   ```

## Frontend Integration
1. Navigate to the Docusaurus directory:
   ```bash
   cd docusaurus
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Add the Chatbot component to your documentation pages by importing it in your MDX files:
   ```jsx
   import Chatbot from '@site/src/components/Chatbot/Chatbot';

   <Chatbot />
   ```

## Configuration
1. Set the backend API URL in the frontend configuration:
   - For development: `http://localhost:8000`
   - For production: your deployed backend URL

2. The chatbot will automatically handle CORS configuration for local development.

## Running the Integrated System
1. Start the Docusaurus development server:
   ```bash
   npm run start
   ```

2. The chatbot will be available on all documentation pages where it's embedded.

## Testing the Integration
1. Visit any documentation page with the chatbot component
2. Type a question in the chat interface
3. Verify that responses are returned with proper citations
4. Test the selected text feature by highlighting text and using the context-aware functionality

## Troubleshooting
- If you get CORS errors, ensure the backend is running and CORS is properly configured
- If API calls fail, verify that all required environment variables are set in the backend
- Check browser console for any frontend errors
- Verify that the backend endpoints are accessible from the frontend origin