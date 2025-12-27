"""Integration tests for database repository."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from sqlmodel import Session

from voice_assistant.db.models import Conversation, Message
from voice_assistant.db.repository import (
    ConversationRepository,
    MessageRepository,
    get_engine,
    init_db,
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    import voice_assistant.db.repository as repo_module

    # Reset the global engine
    original_engine = repo_module._engine
    repo_module._engine = None

    with TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        init_db(db_path)
        engine = get_engine(db_path)
        yield engine

        # Reset engine after test
        repo_module._engine = original_engine


@pytest.fixture
def session(temp_db):
    """Create a database session for testing."""
    with Session(temp_db) as session:
        yield session


class TestConversationRepository:
    """Tests for ConversationRepository."""

    def test_create_conversation(self, session):
        """Should create a new conversation."""
        repo = ConversationRepository(session)
        conv = repo.create()

        assert conv.id is not None
        assert conv.title is None
        assert conv.created_at is not None
        assert conv.updated_at is not None

    def test_create_conversation_with_title(self, session):
        """Should create conversation with title."""
        repo = ConversationRepository(session)
        conv = repo.create(title="Test Chat")

        assert conv.title == "Test Chat"

    def test_get_conversation(self, session):
        """Should get conversation by ID."""
        repo = ConversationRepository(session)
        created = repo.create(title="Find Me")

        found = repo.get(created.id)
        assert found is not None
        assert found.id == created.id
        assert found.title == "Find Me"

    def test_get_nonexistent_conversation(self, session):
        """Should return None for nonexistent ID."""
        repo = ConversationRepository(session)
        found = repo.get("nonexistent-id")
        assert found is None

    def test_get_latest(self, session):
        """Should get most recently updated conversation."""
        repo = ConversationRepository(session)
        conv1 = repo.create(title="First")
        conv2 = repo.create(title="Second")
        conv3 = repo.create(title="Third")

        latest = repo.get_latest()
        assert latest is not None
        assert latest.id == conv3.id

    def test_get_latest_empty_db(self, session):
        """Should return None when no conversations exist."""
        repo = ConversationRepository(session)
        latest = repo.get_latest()
        assert latest is None

    def test_list_all(self, session):
        """Should list conversations ordered by updated_at desc."""
        repo = ConversationRepository(session)
        repo.create(title="A")
        repo.create(title="B")
        repo.create(title="C")

        convs = repo.list_all()
        assert len(convs) == 3
        # Most recent first
        assert convs[0].title == "C"
        assert convs[1].title == "B"
        assert convs[2].title == "A"

    def test_list_all_with_limit(self, session):
        """Should respect limit parameter."""
        repo = ConversationRepository(session)
        for i in range(5):
            repo.create(title=f"Conv {i}")

        convs = repo.list_all(limit=2)
        assert len(convs) == 2

    def test_list_all_with_offset(self, session):
        """Should respect offset parameter."""
        repo = ConversationRepository(session)
        for i in range(5):
            repo.create(title=f"Conv {i}")

        convs = repo.list_all(offset=2, limit=2)
        assert len(convs) == 2
        # Should skip first 2
        assert convs[0].title == "Conv 2"

    def test_update_conversation_title(self, session):
        """Should update conversation title."""
        repo = ConversationRepository(session)
        conv = repo.create(title="Original")
        original_updated = conv.updated_at

        import time

        time.sleep(0.01)  # Ensure time difference

        updated = repo.update(conv.id, title="Updated")
        assert updated is not None
        assert updated.title == "Updated"
        assert updated.updated_at >= original_updated

    def test_update_nonexistent_conversation(self, session):
        """Should return None for nonexistent ID."""
        repo = ConversationRepository(session)
        result = repo.update("nonexistent-id", title="New")
        assert result is None

    def test_touch_updates_timestamp(self, session):
        """Should update updated_at timestamp."""
        repo = ConversationRepository(session)
        conv = repo.create()
        original_updated = conv.updated_at

        import time

        time.sleep(0.01)  # Ensure time difference

        touched = repo.touch(conv.id)
        assert touched is not None
        assert touched.updated_at >= original_updated

    def test_delete_conversation(self, session):
        """Should delete conversation."""
        repo = ConversationRepository(session)
        conv = repo.create(title="Delete Me")

        result = repo.delete(conv.id)
        assert result is True

        # Verify deleted
        found = repo.get(conv.id)
        assert found is None

    def test_delete_nonexistent_conversation(self, session):
        """Should return False for nonexistent ID."""
        repo = ConversationRepository(session)
        result = repo.delete("nonexistent-id")
        assert result is False

    def test_delete_conversation_cascades_messages(self, session):
        """Should delete all messages when conversation is deleted."""
        conv_repo = ConversationRepository(session)
        msg_repo = MessageRepository(session)

        conv = conv_repo.create()
        msg1 = msg_repo.create(conv.id, "user", "Hello")
        msg2 = msg_repo.create(conv.id, "assistant", "Hi")

        conv_repo.delete(conv.id)

        # Messages should be gone
        assert msg_repo.get(msg1.id) is None
        assert msg_repo.get(msg2.id) is None


class TestMessageRepository:
    """Tests for MessageRepository."""

    def test_create_user_message(self, session):
        """Should create user message with STT latency."""
        conv_repo = ConversationRepository(session)
        msg_repo = MessageRepository(session)

        conv = conv_repo.create()
        msg = msg_repo.create(
            conversation_id=conv.id,
            role="user",
            content="Hello",
            stt_latency_ms=150,
        )

        assert msg.id is not None
        assert msg.conversation_id == conv.id
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.stt_latency_ms == 150
        assert msg.llm_latency_ms is None

    def test_create_assistant_message(self, session):
        """Should create assistant message with LLM/TTS latency."""
        conv_repo = ConversationRepository(session)
        msg_repo = MessageRepository(session)

        conv = conv_repo.create()
        msg = msg_repo.create(
            conversation_id=conv.id,
            role="assistant",
            content="Hi there!",
            llm_latency_ms=500,
            tts_latency_ms=200,
        )

        assert msg.role == "assistant"
        assert msg.llm_latency_ms == 500
        assert msg.tts_latency_ms == 200
        assert msg.stt_latency_ms is None

    def test_create_message_updates_conversation_timestamp(self, session):
        """Should update conversation's updated_at when message is created."""
        conv_repo = ConversationRepository(session)
        msg_repo = MessageRepository(session)

        conv = conv_repo.create()
        original_updated = conv.updated_at

        import time

        time.sleep(0.01)

        msg_repo.create(conv.id, "user", "Test")

        # Refresh conversation
        updated_conv = conv_repo.get(conv.id)
        assert updated_conv.updated_at >= original_updated

    def test_get_message(self, session):
        """Should get message by ID."""
        conv_repo = ConversationRepository(session)
        msg_repo = MessageRepository(session)

        conv = conv_repo.create()
        created = msg_repo.create(conv.id, "user", "Find me")

        found = msg_repo.get(created.id)
        assert found is not None
        assert found.content == "Find me"

    def test_get_nonexistent_message(self, session):
        """Should return None for nonexistent ID."""
        msg_repo = MessageRepository(session)
        found = msg_repo.get("nonexistent-id")
        assert found is None

    def test_list_by_conversation(self, session):
        """Should list messages for conversation in chronological order."""
        conv_repo = ConversationRepository(session)
        msg_repo = MessageRepository(session)

        conv = conv_repo.create()
        msg_repo.create(conv.id, "user", "First")
        msg_repo.create(conv.id, "assistant", "Second")
        msg_repo.create(conv.id, "user", "Third")

        messages = msg_repo.list_by_conversation(conv.id)
        assert len(messages) == 3
        assert messages[0].content == "First"
        assert messages[1].content == "Second"
        assert messages[2].content == "Third"

    def test_list_by_conversation_only_includes_correct_conversation(self, session):
        """Should only return messages from specified conversation."""
        conv_repo = ConversationRepository(session)
        msg_repo = MessageRepository(session)

        conv1 = conv_repo.create()
        conv2 = conv_repo.create()

        msg_repo.create(conv1.id, "user", "Conv1 Msg")
        msg_repo.create(conv2.id, "user", "Conv2 Msg")

        messages = msg_repo.list_by_conversation(conv1.id)
        assert len(messages) == 1
        assert messages[0].content == "Conv1 Msg"

    def test_list_by_conversation_with_limit(self, session):
        """Should respect limit parameter."""
        conv_repo = ConversationRepository(session)
        msg_repo = MessageRepository(session)

        conv = conv_repo.create()
        for i in range(5):
            msg_repo.create(conv.id, "user", f"Msg {i}")

        messages = msg_repo.list_by_conversation(conv.id, limit=2)
        assert len(messages) == 2

    def test_update_latency(self, session):
        """Should update latency fields."""
        conv_repo = ConversationRepository(session)
        msg_repo = MessageRepository(session)

        conv = conv_repo.create()
        msg = msg_repo.create(conv.id, "assistant", "Test")

        updated = msg_repo.update_latency(
            msg.id,
            llm_latency_ms=500,
            tts_latency_ms=200,
        )

        assert updated is not None
        assert updated.llm_latency_ms == 500
        assert updated.tts_latency_ms == 200

    def test_update_latency_nonexistent_message(self, session):
        """Should return None for nonexistent ID."""
        msg_repo = MessageRepository(session)
        result = msg_repo.update_latency("nonexistent-id", llm_latency_ms=100)
        assert result is None

    def test_delete_message(self, session):
        """Should delete message."""
        conv_repo = ConversationRepository(session)
        msg_repo = MessageRepository(session)

        conv = conv_repo.create()
        msg = msg_repo.create(conv.id, "user", "Delete me")

        result = msg_repo.delete(msg.id)
        assert result is True

        # Verify deleted
        found = msg_repo.get(msg.id)
        assert found is None

    def test_delete_nonexistent_message(self, session):
        """Should return False for nonexistent ID."""
        msg_repo = MessageRepository(session)
        result = msg_repo.delete("nonexistent-id")
        assert result is False


class TestForeignKeyConstraint:
    """Tests for foreign key constraints."""

    def test_message_requires_valid_conversation_id(self, session):
        """Message should require valid conversation (FK enforced)."""
        from sqlalchemy.exc import IntegrityError

        msg_repo = MessageRepository(session)

        # With FK constraints enabled, this should raise an IntegrityError
        with pytest.raises(IntegrityError):
            msg_repo.create(
                conversation_id="invalid-conv-id",
                role="user",
                content="Orphan",
            )
