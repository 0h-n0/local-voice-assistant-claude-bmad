"""Integration tests for conversation REST API endpoints."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from sqlmodel import Session

from voice_assistant.db import (
    ConversationRepository,
    MessageRepository,
    get_engine,
    init_db,
)
from voice_assistant.main import app
import voice_assistant.db.repository as repo_module


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    # Reset the global engine
    original_engine = repo_module._engine
    repo_module._engine = None

    with TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        init_db(db_path)
        yield
        # Reset engine after test
        repo_module._engine = original_engine


@pytest.fixture
def client(temp_db):
    """Create a test client with a temporary database."""
    return TestClient(app)


@pytest.fixture
def sample_conversation(temp_db):
    """Create a sample conversation with messages."""
    engine = get_engine()
    with Session(engine) as session:
        conv_repo = ConversationRepository(session)
        msg_repo = MessageRepository(session)

        conv = conv_repo.create(title="Test Conversation")
        msg_repo.create(conv.id, "user", "Hello", stt_latency_ms=150)
        msg_repo.create(
            conv.id, "assistant", "Hi there!", llm_latency_ms=500, tts_latency_ms=200
        )
        return conv.id


class TestGetLatestConversation:
    """Tests for GET /api/v1/conversations/latest."""

    def test_returns_404_when_no_conversations(self, client):
        """Should return 404 when no conversations exist."""
        response = client.get("/api/v1/conversations/latest")
        assert response.status_code == 404
        assert response.json()["detail"] == "No conversations found"

    def test_returns_latest_conversation(self, client, sample_conversation):
        """Should return the latest conversation with messages."""
        response = client.get("/api/v1/conversations/latest")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == sample_conversation
        assert data["title"] == "Test Conversation"
        assert len(data["messages"]) == 2

        # Verify message order (chronological)
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][0]["content"] == "Hello"
        assert data["messages"][0]["stt_latency_ms"] == 150

        assert data["messages"][1]["role"] == "assistant"
        assert data["messages"][1]["content"] == "Hi there!"
        assert data["messages"][1]["llm_latency_ms"] == 500
        assert data["messages"][1]["tts_latency_ms"] == 200

    def test_returns_most_recent_conversation(self, client, temp_db):
        """Should return the most recently updated conversation."""
        engine = get_engine()
        with Session(engine) as session:
            conv_repo = ConversationRepository(session)

            conv1 = conv_repo.create(title="First")
            import time

            time.sleep(0.01)
            conv2 = conv_repo.create(title="Second")

        response = client.get("/api/v1/conversations/latest")
        assert response.status_code == 200
        assert response.json()["title"] == "Second"


class TestGetConversation:
    """Tests for GET /api/v1/conversations/{conversation_id}."""

    def test_returns_404_for_nonexistent_conversation(self, client):
        """Should return 404 when conversation doesn't exist."""
        response = client.get("/api/v1/conversations/nonexistent-id")
        assert response.status_code == 404
        assert response.json()["detail"] == "Conversation not found"

    def test_returns_conversation_with_messages(self, client, sample_conversation):
        """Should return the specified conversation with messages."""
        response = client.get(f"/api/v1/conversations/{sample_conversation}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == sample_conversation
        assert data["title"] == "Test Conversation"
        assert len(data["messages"]) == 2

    def test_returns_empty_messages_for_new_conversation(self, client, temp_db):
        """Should return conversation with empty messages list."""
        engine = get_engine()
        with Session(engine) as session:
            conv_repo = ConversationRepository(session)
            conv = conv_repo.create(title="Empty")

        response = client.get(f"/api/v1/conversations/{conv.id}")
        assert response.status_code == 200
        assert response.json()["messages"] == []
