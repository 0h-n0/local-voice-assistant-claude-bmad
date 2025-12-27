"""Repository layer for database operations.

Provides CRUD operations for Conversation and Message entities.
Uses SQLite for local persistence (data/voice_assistant.db).
"""

from collections.abc import Generator
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine, select

from voice_assistant.db.models import Conversation, Message, generate_id, utc_now


def _enable_sqlite_fk(dbapi_connection, connection_record):
    """Enable foreign key constraints for SQLite connections."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Default database path
DEFAULT_DB_PATH = Path("data/voice_assistant.db")

# Module-level engine (initialized on first use)
_engine = None


def get_engine(db_path: Path | None = None):
    """Get or create the database engine.

    Args:
        db_path: Optional custom database path. Defaults to data/voice_assistant.db

    Returns:
        SQLModel engine instance
    """
    global _engine
    if _engine is None:
        path = db_path or DEFAULT_DB_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        database_url = f"sqlite:///{path}"
        _engine = create_engine(
            database_url,
            echo=False,
            connect_args={"check_same_thread": False},
        )
        # Enable foreign key constraints for SQLite
        event.listen(_engine, "connect", _enable_sqlite_fk)
    return _engine


def init_db(db_path: Path | None = None) -> None:
    """Initialize the database by creating all tables.

    Args:
        db_path: Optional custom database path
    """
    engine = get_engine(db_path)
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Get a database session.

    Yields:
        Database session that auto-commits on success
    """
    engine = get_engine()
    with Session(engine) as session:
        yield session


class ConversationRepository:
    """Repository for Conversation CRUD operations."""

    def __init__(self, session: Session):
        """Initialize repository with a database session.

        Args:
            session: SQLModel session for database operations
        """
        self.session = session

    def create(self, title: str | None = None) -> Conversation:
        """Create a new conversation.

        Args:
            title: Optional conversation title

        Returns:
            Created Conversation instance
        """
        conversation = Conversation(
            id=generate_id(),
            title=title,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        self.session.add(conversation)
        self.session.commit()
        self.session.refresh(conversation)
        return conversation

    def get(self, conversation_id: str) -> Conversation | None:
        """Get a conversation by ID.

        Args:
            conversation_id: The conversation ID

        Returns:
            Conversation if found, None otherwise
        """
        return self.session.get(Conversation, conversation_id)

    def get_latest(self) -> Conversation | None:
        """Get the most recently updated conversation.

        Returns:
            Latest Conversation if any exist, None otherwise
        """
        statement = select(Conversation).order_by(Conversation.updated_at.desc())
        return self.session.exec(statement).first()

    def list_all(self, limit: int = 50, offset: int = 0) -> list[Conversation]:
        """List conversations ordered by updated_at descending.

        Args:
            limit: Maximum number of conversations to return
            offset: Number of conversations to skip

        Returns:
            List of Conversation instances
        """
        statement = (
            select(Conversation)
            .order_by(Conversation.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def update(
        self, conversation_id: str, title: str | None = None
    ) -> Conversation | None:
        """Update a conversation.

        Args:
            conversation_id: The conversation ID
            title: New title (optional)

        Returns:
            Updated Conversation if found, None otherwise
        """
        conversation = self.get(conversation_id)
        if conversation is None:
            return None

        if title is not None:
            conversation.title = title
        conversation.updated_at = utc_now()

        self.session.add(conversation)
        self.session.commit()
        self.session.refresh(conversation)
        return conversation

    def touch(self, conversation_id: str) -> Conversation | None:
        """Update the updated_at timestamp of a conversation.

        Args:
            conversation_id: The conversation ID

        Returns:
            Updated Conversation if found, None otherwise
        """
        return self.update(conversation_id)

    def delete(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages.

        Args:
            conversation_id: The conversation ID

        Returns:
            True if deleted, False if not found
        """
        conversation = self.get(conversation_id)
        if conversation is None:
            return False

        # Delete all messages first (cascade)
        statement = select(Message).where(Message.conversation_id == conversation_id)
        messages = self.session.exec(statement).all()
        for message in messages:
            self.session.delete(message)

        self.session.delete(conversation)
        self.session.commit()
        return True


class MessageRepository:
    """Repository for Message CRUD operations."""

    def __init__(self, session: Session):
        """Initialize repository with a database session.

        Args:
            session: SQLModel session for database operations
        """
        self.session = session

    def create(
        self,
        conversation_id: str,
        role: Literal["user", "assistant"],
        content: str,
        stt_latency_ms: int | None = None,
        llm_latency_ms: int | None = None,
        tts_latency_ms: int | None = None,
    ) -> Message:
        """Create a new message.

        Args:
            conversation_id: Parent conversation ID
            role: Message role (user or assistant)
            content: Message text content
            stt_latency_ms: STT latency for user messages
            llm_latency_ms: LLM latency for assistant messages
            tts_latency_ms: TTS latency for assistant messages

        Returns:
            Created Message instance
        """
        message = Message(
            id=generate_id(),
            conversation_id=conversation_id,
            role=role,
            content=content,
            stt_latency_ms=stt_latency_ms,
            llm_latency_ms=llm_latency_ms,
            tts_latency_ms=tts_latency_ms,
            created_at=utc_now(),
        )
        self.session.add(message)
        self.session.commit()
        self.session.refresh(message)

        # Update conversation's updated_at
        conversation_repo = ConversationRepository(self.session)
        conversation_repo.touch(conversation_id)

        return message

    def get(self, message_id: str) -> Message | None:
        """Get a message by ID.

        Args:
            message_id: The message ID

        Returns:
            Message if found, None otherwise
        """
        return self.session.get(Message, message_id)

    def list_by_conversation(
        self, conversation_id: str, limit: int = 100, offset: int = 0
    ) -> list[Message]:
        """List messages for a conversation ordered by created_at ascending.

        Args:
            conversation_id: The conversation ID
            limit: Maximum number of messages to return
            offset: Number of messages to skip

        Returns:
            List of Message instances
        """
        statement = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def update_latency(
        self,
        message_id: str,
        stt_latency_ms: int | None = None,
        llm_latency_ms: int | None = None,
        tts_latency_ms: int | None = None,
    ) -> Message | None:
        """Update latency fields for a message.

        Args:
            message_id: The message ID
            stt_latency_ms: STT latency to update
            llm_latency_ms: LLM latency to update
            tts_latency_ms: TTS latency to update

        Returns:
            Updated Message if found, None otherwise
        """
        message = self.get(message_id)
        if message is None:
            return None

        if stt_latency_ms is not None:
            message.stt_latency_ms = stt_latency_ms
        if llm_latency_ms is not None:
            message.llm_latency_ms = llm_latency_ms
        if tts_latency_ms is not None:
            message.tts_latency_ms = tts_latency_ms

        self.session.add(message)
        self.session.commit()
        self.session.refresh(message)
        return message

    def delete(self, message_id: str) -> bool:
        """Delete a message.

        Args:
            message_id: The message ID

        Returns:
            True if deleted, False if not found
        """
        message = self.get(message_id)
        if message is None:
            return False

        self.session.delete(message)
        self.session.commit()
        return True
