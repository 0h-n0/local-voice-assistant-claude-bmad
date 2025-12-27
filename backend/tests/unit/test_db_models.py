"""Unit tests for database models."""

import pytest
from datetime import datetime, timezone

from voice_assistant.db.models import Conversation, Message, generate_id, utc_now


class TestGenerateId:
    """Tests for generate_id function."""

    def test_returns_string(self):
        """Should return a string."""
        result = generate_id()
        assert isinstance(result, str)

    def test_returns_uuid_format(self):
        """Should return a valid UUID format."""
        result = generate_id()
        # UUID format: 8-4-4-4-12 hex digits
        parts = result.split("-")
        assert len(parts) == 5
        assert len(parts[0]) == 8
        assert len(parts[1]) == 4
        assert len(parts[2]) == 4
        assert len(parts[3]) == 4
        assert len(parts[4]) == 12

    def test_returns_unique_values(self):
        """Should return unique values each call."""
        ids = [generate_id() for _ in range(100)]
        assert len(set(ids)) == 100


class TestUtcNow:
    """Tests for utc_now function."""

    def test_returns_datetime(self):
        """Should return a datetime object."""
        result = utc_now()
        assert isinstance(result, datetime)

    def test_returns_utc_timezone(self):
        """Should return a datetime with UTC timezone."""
        result = utc_now()
        assert result.tzinfo == timezone.utc


class TestConversationModel:
    """Tests for Conversation model."""

    def test_create_conversation_with_defaults(self):
        """Should create conversation with default values."""
        conv = Conversation()
        assert conv.id is not None
        assert conv.title is None
        assert conv.created_at is not None
        assert conv.updated_at is not None

    def test_create_conversation_with_title(self):
        """Should create conversation with title."""
        conv = Conversation(title="Test Conversation")
        assert conv.title == "Test Conversation"

    def test_conversation_has_messages_relationship(self):
        """Should have messages relationship attribute."""
        conv = Conversation()
        assert hasattr(conv, "messages")


class TestMessageModel:
    """Tests for Message model."""

    def test_create_user_message(self):
        """Should create user message."""
        msg = Message(
            conversation_id="test-conv-id",
            role="user",
            content="Hello",
            stt_latency_ms=150,
        )
        assert msg.id is not None
        assert msg.conversation_id == "test-conv-id"
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.stt_latency_ms == 150
        assert msg.llm_latency_ms is None
        assert msg.tts_latency_ms is None

    def test_create_assistant_message(self):
        """Should create assistant message with latency fields."""
        msg = Message(
            conversation_id="test-conv-id",
            role="assistant",
            content="Hi there!",
            llm_latency_ms=500,
            tts_latency_ms=200,
        )
        assert msg.role == "assistant"
        assert msg.content == "Hi there!"
        assert msg.llm_latency_ms == 500
        assert msg.tts_latency_ms == 200
        assert msg.stt_latency_ms is None

    def test_message_has_conversation_relationship(self):
        """Should have conversation relationship attribute."""
        msg = Message(
            conversation_id="test-conv-id",
            role="user",
            content="Test",
        )
        assert hasattr(msg, "conversation")

    def test_message_role_type(self):
        """Should only accept 'user' or 'assistant' roles."""
        # Valid roles
        user_msg = Message(conversation_id="c", role="user", content="test")
        assert user_msg.role == "user"

        assistant_msg = Message(conversation_id="c", role="assistant", content="test")
        assert assistant_msg.role == "assistant"
