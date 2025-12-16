---
id: 2
title: "Agentic RAG Backend"
stage: plan
date_iso: 2025-12-15
surface: agent
model: claude-sonnet-4-5-20250929
feature: "001-agent-rag-backend"
branch: "001-agent-rag-backend"
user: "maliaraees"
command: "/sp.plan"
labels: ["plan", "rag", "agent", "fastapi", "qdrant", "postgres"]
links:
  spec: "specs/001-agent-rag-backend/spec.md"
  ticket: null
  adr: null
  pr: null
files_yaml: |
  - specs/001-agent-rag-backend/plan.md
  - specs/001-agent-rag-backend/research.md
  - specs/001-agent-rag-backend/data-model.md
  - specs/001-agent-rag-backend/contracts/api-contracts.md
  - specs/001-agent-rag-backend/quickstart.md
tests_yaml: |
  - Architecture design review
  - API contract verification
  - Data model validation
  - Technical approach validation
prompt_text: "Agentic RAG Backend

Approach:
Implement an agentic RAG architecture where an OpenAI Agent coordinates
retrieval from Qdrant and answer generation via Gemini, exposed through
a FastAPI service layer with persistence in Neon Postgres.

Steps:
1. Load environment variables (Gemini API key, Qdrant config, Neon DSN)
2. Initialize Qdrant retrieval client (read-only)
3. Define retrieval tool callable by the agent
4. Configure Gemini LLM as the agent’s reasoning engine
5. Define agent system instructions enforcing grounded responses
6. Integrate retrieval tool into the agent workflow
7. Implement FastAPI endpoint for RAG queries
8. Execute retrieval → generation pipeline per request
9. Persist query logs, retrieved chunk IDs, and responses in Neon
10. Handle errors, timeouts, and empty retrieval cases gracefully

Verification:
- Agent always invokes retrieval before generating answers
- Responses cite retrieved chunks accurately
- No hallucinated content outside retrieved context
- FastAPI endpoint returns deterministic, repeatable results
- Logs in Neon match API activity

Deliverables:
- Agent configuration and tool definitions
- FastAPI service with RAG endpoint
- Neon schema for query and response logging
- Documentation of agent behavior and limitations"
response_text: "Successfully created comprehensive implementation plan with technical context, constitution check, project structure, research summary, data model, API contracts, and quickstart guide. The plan includes all required components for the agentic RAG backend with OpenAI Agent SDK, FastAPI, Qdrant, and Neon Postgres integration."
outcome: "Successfully created comprehensive implementation plan with technical context, constitution check, project structure, research summary, data model, API contracts, and quickstart guide. The plan includes all required components for the agentic RAG backend with OpenAI Agent SDK, FastAPI, Qdrant, and Neon Postgres integration."
evaluation: "The implementation plan meets all requirements: it defines the technical approach, specifies dependencies, outlines the project structure, and includes all necessary supporting documents. The plan aligns with the feature specification and constraints. All Phase 0 and Phase 1 deliverables have been created successfully."
---

# Implementation Plan: Agent-Based RAG Backend with FastAPI

**Branch**: `001-agent-rag-backend` | **Date**: 2025-12-15 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-agent-rag-backend/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Create an agentic RAG system that uses the OpenAI Agent SDK to orchestrate retrieval from Qdrant and answer generation via Gemini, exposed through a FastAPI service layer with persistence in Neon Postgres. The system will ensure all responses are grounded in retrieved content with proper citations to source materials (URL, module, chunk_id).

## Technical Context

**Language/Version**: Python 3.10+ (as specified in feature constraints for compatibility with ROS 2 integration)
**Primary Dependencies**: OpenAI Agent SDK, FastAPI, Qdrant client library, Neon Postgres client, Google Generative AI (for Gemini), Pydantic, SQLAlchemy
**Storage**: Qdrant vector database (for content retrieval), Neon Serverless Postgres (for conversation logs and query history)
**Testing**: pytest for unit and integration testing
**Target Platform**: Linux server environment (for backend API services)
**Project Type**: Web API service with agent orchestration
**Performance Goals**: <5 second response time for queries, support 100+ concurrent requests, 95% uptime
**Constraints**: Must operate within Qdrant Cloud Free Tier limits, Gemini API rate limits, Neon Postgres connection limits, responses must be grounded in retrieved content only
**Scale/Scope**: Support technical learning platform with book content, handle general and scoped queries, maintain conversation state for debugging

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

This feature (agentic RAG backend) supports the AI & Humanoid Robotics book content by providing a technical learning platform for backend and AI engineers. The system will be built following general software engineering best practices:

- Code will follow Python best practices and PEP8 standards (as per Module 1 Constitution)
- Dependencies will be managed properly with pip
- Documentation will be clear and maintainable
- The system will be reproducible and operate within free-tier limits as specified
- Proper error handling will be implemented for robust operation
- Testing will be included to ensure reliability
- Performance will meet the specified goals (<5 second response time)
- The system will be designed for maintainability and debugging (with conversation logs)

This feature does not directly implement robotics concepts but provides infrastructure for learning about agentic systems, which aligns with Module 4's focus on AI-Robot brains and VLA systems.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── rag_agent/                 # Main agentic RAG implementation
│   ├── __init__.py
│   ├── agent.py               # OpenAI Agent SDK configuration and orchestration
│   ├── tools.py               # Retrieval tool definitions for the agent
│   ├── models.py              # Pydantic models for requests/responses
│   ├── config.py              # Configuration for Gemini, Qdrant, Neon
│   └── utils.py               # Utility functions
├── api/                       # FastAPI service layer
│   ├── __init__.py
│   ├── main.py                # FastAPI app definition
│   ├── routers/               # API route definitions
│   │   └── rag.py             # RAG query endpoints
│   └── middleware/            # Request/response processing
├── database/                  # Neon Postgres integration
│   ├── __init__.py
│   ├── models.py              # SQLAlchemy models for logs and conversations
│   ├── schemas.py             # Pydantic schemas for database entities
│   └── session.py             # Database session management
├── retrieval/                 # Qdrant retrieval functionality
│   ├── __init__.py
│   ├── client.py              # Qdrant client initialization and operations
│   └── search.py              # Search and retrieval logic
├── tests/                     # Test suite
│   ├── test_agent.py          # Agent functionality tests
│   ├── test_api.py            # API endpoint tests
│   ├── test_retrieval.py      # Retrieval functionality tests
│   └── conftest.py            # Test configuration
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
└── README.md                  # Service documentation
```

**Structure Decision**: Web API service approach with clear separation of concerns. The agent orchestration layer handles the retrieval-generation workflow, while the API layer provides the interface for external systems. The database layer handles persistence of conversations and query logs, and the retrieval layer manages interaction with Qdrant. This structure follows standard FastAPI project organization and allows for independent testing and development of each component.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations identified. The implementation follows the project's foundational guidelines for each module and maintains compatibility with the AI & Humanoid Robotics learning platform requirements.