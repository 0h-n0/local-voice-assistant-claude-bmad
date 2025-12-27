"""FastAPI application entry point for Voice Assistant"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session

from voice_assistant.api.websocket import router as ws_router
from voice_assistant.core.config import settings
from voice_assistant.core.logging import configure_logging, get_logger
from voice_assistant.db import (
    ConversationRepository,
    MessageRepository,
    get_engine,
    init_db,
)

logger = get_logger(__name__)


class MessageResponse(BaseModel):
    """Response model for a message."""

    id: str
    role: str
    content: str
    stt_latency_ms: int | None
    llm_latency_ms: int | None
    tts_latency_ms: int | None
    created_at: datetime


class ConversationResponse(BaseModel):
    """Response model for a conversation."""

    id: str
    title: str | None
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse]


class ConversationListItem(BaseModel):
    """Response model for conversation list item (without messages)."""

    id: str
    title: str | None
    created_at: datetime
    updated_at: datetime


class ConversationListMeta(BaseModel):
    """Pagination metadata."""

    total: int
    limit: int
    offset: int


class ConversationListResponse(BaseModel):
    """Response model for conversation list."""

    data: list[ConversationListItem]
    meta: ConversationListMeta


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup/shutdown."""
    # Startup
    configure_logging()
    # Initialize database
    init_db()
    logger.info("database_initialized")
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


@app.get("/api/v1/conversations")
async def list_conversations(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ConversationListResponse:
    """Get list of conversations with pagination.

    Args:
        limit: Maximum number of conversations (1-100, default: 20)
        offset: Number of conversations to skip (default: 0)

    Returns:
        List of conversations with pagination metadata.
    """
    with Session(get_engine()) as session:
        conv_repo = ConversationRepository(session)
        conversations = conv_repo.list_all(limit=limit, offset=offset)
        total = conv_repo.count()

        return ConversationListResponse(
            data=[
                ConversationListItem(
                    id=conv.id,
                    title=conv.title,
                    created_at=conv.created_at,
                    updated_at=conv.updated_at,
                )
                for conv in conversations
            ],
            meta=ConversationListMeta(
                total=total,
                limit=limit,
                offset=offset,
            ),
        )


@app.get("/api/v1/conversations/latest")
async def get_latest_conversation() -> ConversationResponse | None:
    """Get the most recent conversation with its messages.

    Returns:
        The latest conversation with messages, or null if none exist.

    Raises:
        HTTPException: If no conversations exist (404).
    """
    with Session(get_engine()) as session:
        conv_repo = ConversationRepository(session)
        msg_repo = MessageRepository(session)

        latest = conv_repo.get_latest()
        if latest is None:
            raise HTTPException(status_code=404, detail="No conversations found")

        messages = msg_repo.list_by_conversation(latest.id, limit=100)

        return ConversationResponse(
            id=latest.id,
            title=latest.title,
            created_at=latest.created_at,
            updated_at=latest.updated_at,
            messages=[
                MessageResponse(
                    id=msg.id,
                    role=msg.role,
                    content=msg.content,
                    stt_latency_ms=msg.stt_latency_ms,
                    llm_latency_ms=msg.llm_latency_ms,
                    tts_latency_ms=msg.tts_latency_ms,
                    created_at=msg.created_at,
                )
                for msg in messages
            ],
        )


@app.get("/api/v1/conversations/{conversation_id}")
async def get_conversation(conversation_id: str) -> ConversationResponse:
    """Get a specific conversation with its messages.

    Args:
        conversation_id: The conversation ID.

    Returns:
        The conversation with messages.

    Raises:
        HTTPException: If conversation not found (404).
    """
    with Session(get_engine()) as session:
        conv_repo = ConversationRepository(session)
        msg_repo = MessageRepository(session)

        conv = conv_repo.get(conversation_id)
        if conv is None:
            raise HTTPException(status_code=404, detail="Conversation not found")

        messages = msg_repo.list_by_conversation(conversation_id, limit=100)

        return ConversationResponse(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            messages=[
                MessageResponse(
                    id=msg.id,
                    role=msg.role,
                    content=msg.content,
                    stt_latency_ms=msg.stt_latency_ms,
                    llm_latency_ms=msg.llm_latency_ms,
                    tts_latency_ms=msg.tts_latency_ms,
                    created_at=msg.created_at,
                )
                for msg in messages
            ],
        )
