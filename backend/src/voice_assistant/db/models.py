"""SQLModel models for conversation persistence.

Schema design follows Architecture.md specifications:
- Table names: snake_case plural (conversations, messages)
- Column names: snake_case
- Foreign keys: {table_singular}_id
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Literal
from uuid import uuid4

from sqlmodel import Field, Relationship, SQLModel

# Type alias for message role
MessageRole = Literal["user", "assistant"]


def generate_id() -> str:
    """Generate a UUID-based ID for database records."""
    return str(uuid4())


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


class Conversation(SQLModel, table=True):
    """Conversation model representing a chat session.

    Attributes:
        id: UUID-based primary key
        title: Optional conversation title (auto-generated from first message if None)
        created_at: When the conversation was created
        updated_at: When the conversation was last updated
    """

    __tablename__ = "conversations"
    __table_args__ = {"extend_existing": True}

    id: str = Field(default_factory=generate_id, primary_key=True)
    title: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    # Relationship to messages
    messages: list["Message"] = Relationship(back_populates="conversation")


class Message(SQLModel, table=True):
    """Message model representing a single message in a conversation.

    Attributes:
        id: UUID-based primary key
        conversation_id: Foreign key to parent conversation
        role: Message role (user or assistant)
        content: Message text content
        stt_latency_ms: Speech-to-text latency in milliseconds (user messages)
        llm_latency_ms: LLM response latency in milliseconds (assistant messages)
        tts_latency_ms: Text-to-speech latency in milliseconds (assistant messages)
        created_at: When the message was created
    """

    __tablename__ = "messages"
    __table_args__ = {"extend_existing": True}

    id: str = Field(default_factory=generate_id, primary_key=True)
    conversation_id: str = Field(foreign_key="conversations.id", index=True)
    role: str  # "user" or "assistant" - stored as string in DB
    content: str
    stt_latency_ms: int | None = None
    llm_latency_ms: int | None = None
    tts_latency_ms: int | None = None
    created_at: datetime = Field(default_factory=utc_now)

    # Relationship to conversation
    conversation: Conversation | None = Relationship(back_populates="messages")
