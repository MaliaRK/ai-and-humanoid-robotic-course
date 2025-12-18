from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from .routers import rag

# Set up comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set up rate limiter
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for FastAPI application.
    This runs startup and shutdown events.
    """
    logger.info("Starting up RAG API service...")
    logger.info("Initializing services and connections...")
    # Any startup logic can go here
    yield
    logger.info("Shutting down RAG API service...")
    logger.info("Cleaning up resources...")

# Create FastAPI app instance
app = FastAPI(
    title="Agentic RAG Backend API",
    description="API for agent-based RAG system using OpenAI Agent SDK, Qdrant, and Gemini",
    version="1.0.0",
    lifespan=lifespan
)

# Set up rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://ai-and-humanoid-robotic-course.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add comprehensive request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    request_id = f"req_{int(start_time * 1000000)}"  # Create a simple request ID
    logger.info(f"[{request_id}] {request.method} {request.url.path} - Started")

    # Note: We don't read request.body() here as it would consume the stream
    # and make it unavailable for Pydantic model parsing in endpoints

    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        logger.info(f"[{request_id}] {request.method} {request.url.path} - Status: {response.status_code} - Process time: {process_time:.2f}s")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"[{request_id}] {request.method} {request.url.path} - Error: {str(e)} - Process time: {process_time:.2f}s")
        raise

# Include routers
app.include_router(rag.router, prefix="/api/v1", tags=["rag"])

@app.get("/")
def read_root():
    """
    Root endpoint to check if the service is running.
    """
    return {"message": "Agentic RAG Backend API is running"}

@app.get("/health")
def health_check():
    """
    Health check endpoint to verify service status.
    """
    return {
        "status": "healthy",
        "service": "Agentic RAG Backend API",
        "version": "1.0.0"
    }

# Global exception handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Invalid request parameters",
            "details": exc.errors()
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP_ERROR",
            "message": exc.detail,
            "code": exc.detail
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"General error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An internal server error occurred",
            "code": "INTERNAL_ERROR"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)