# Research: Agentic RAG Backend with FastAPI

## Decision: OpenAI Agent SDK Integration
**Rationale**: The feature specification explicitly requires using the OpenAI Agent SDK to orchestrate retrieval and generation. This provides a standardized way to create agents that can use tools (like Qdrant retrieval) and generate responses using LLMs.

**Alternatives considered**:
- Custom agent implementation: Would require more development time and reinvent existing patterns
- LangChain agents: Not specifically mentioned in requirements
- Anthropic Claude as agent: Contradicts requirement for OpenAI Agent SDK

## Decision: Gemini LLM as Reasoning Engine
**Rationale**: The feature specification explicitly requires using Gemini as the primary reasoning model, accessed via API key in environment variables. This ensures compatibility with Google's LLM capabilities and meets the specified constraint.

**Alternatives considered**:
- OpenAI GPT models: Contradicts requirement for Gemini
- Open-source models (Llama, etc.): Contradicts requirement for Gemini
- Anthropic Claude: Contradicts requirement for Gemini

## Decision: Qdrant for Vector Storage
**Rationale**: The feature specification explicitly requires using Qdrant for retrieval, with read-only access. Qdrant is a proven vector database solution that integrates well with Python applications.

**Alternatives considered**:
- Pinecone: Contradicts requirement for Qdrant
- Weaviate: Contradicts requirement for Qdrant
- Chroma: Contradicts requirement for Qdrant
- Elasticsearch: Contradicts requirement for Qdrant

## Decision: Neon Serverless Postgres for Persistence
**Rationale**: The feature specification explicitly requires using Neon Serverless Postgres for storing conversation state and query logs. Neon provides serverless Postgres with auto-scaling and branch capabilities.

**Alternatives considered**:
- Traditional Postgres: Contradicts requirement for Neon
- MySQL: Contradicts requirement for Postgres
- MongoDB: Contradicts requirement for Postgres
- Redis: Not suitable for structured conversation logs

## Decision: FastAPI for Web Service Layer
**Rationale**: FastAPI provides high-performance, easy-to-use web API framework with automatic OpenAPI documentation. It's well-suited for ML/AI backend services and has excellent async support.

**Alternatives considered**:
- Flask: Less performant, less async-friendly than FastAPI
- Django: Overkill for API-only service, heavier than needed
- Express.js: Contradicts Python requirement
- Starlette: Too low-level, FastAPI provides better developer experience

## Decision: Agent Tool Integration Pattern
**Rationale**: The agent needs to use a retrieval tool before generating responses. This pattern ensures all responses are grounded in retrieved content, meeting the requirement for citation-aware, grounded responses.

**Implementation approach**:
- Create a retrieval tool that queries Qdrant
- Configure the agent to use this tool when processing queries
- Ensure the agent cannot generate responses without using the tool
- Format retrieved content for the LLM with proper source metadata

## Decision: Response Citation Format
**Rationale**: The system must return answers with source metadata (URL, module, chunk_id) as specified in requirements. This ensures transparency and verifiability of responses.

**Implementation approach**:
- Include source metadata in retrieved chunks
- Format citations in responses using standard academic citation patterns
- Maintain citation links back to original content
- Validate citations exist before returning responses

## Decision: Error Handling Strategy
**Rationale**: The system must handle various failure modes gracefully (Qdrant unavailable, Gemini API limits, Neon Postgres issues) to maintain reliability.

**Implementation approach**:
- Implement retry logic with exponential backoff
- Provide graceful degradation when services are unavailable
- Return informative error messages to clients
- Log errors for debugging and monitoring

## Decision: Conversation State Management
**Rationale**: The system needs to track conversation state for debugging and analytics as specified in requirements.

**Implementation approach**:
- Store conversation history in Neon Postgres
- Include query, response, and metadata
- Maintain conversation context for multi-turn interactions
- Implement cleanup for old conversations to manage storage