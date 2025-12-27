"""FastAPI application entry point for Voice Assistant"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from voice_assistant.api.websocket import router as ws_router
from voice_assistant.core.config import settings
from voice_assistant.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup/shutdown."""
    # Startup
    configure_logging()
    yield
    # Shutdown (nothing to clean up for now)


app = FastAPI(
    title="Voice Assistant API",
    description="日本語特化ローカル音声対話アシスタント",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
# NOTE: allow_methods/allow_headers are permissive for development.
# For production, restrict to: ["GET", "POST", "DELETE"] and specific headers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
)


# Include WebSocket router
app.include_router(ws_router)


@app.get("/api/v1/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        dict with status "ok" if the service is healthy.
    """
    return {"status": "ok"}
