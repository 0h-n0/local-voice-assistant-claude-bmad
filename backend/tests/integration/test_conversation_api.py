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


class TestListConversations:
    """Tests for GET /api/v1/conversations."""

    def test_returns_empty_list_when_no_conversations(self, client):
        """Should return empty list (not 404) when no conversations exist."""
        response = client.get("/api/v1/conversations")
        assert response.status_code == 200

        data = response.json()
        assert data["data"] == []
        assert data["meta"]["total"] == 0
        assert data["meta"]["limit"] == 20
        assert data["meta"]["offset"] == 0

    def test_returns_conversations_list(self, client, sample_conversation):
        """Should return list of conversations."""
        response = client.get("/api/v1/conversations")
        assert response.status_code == 200

        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == sample_conversation
        assert data["data"][0]["title"] == "Test Conversation"
        assert "messages" not in data["data"][0]  # No messages in list view
        assert data["meta"]["total"] == 1

    def test_conversations_sorted_by_updated_at_desc(self, client, temp_db):
        """Should return conversations sorted by updated_at descending."""
        import time

        engine = get_engine()
        with Session(engine) as session:
            conv_repo = ConversationRepository(session)

            conv1 = conv_repo.create(title="First")
            time.sleep(0.01)
            conv2 = conv_repo.create(title="Second")
            time.sleep(0.01)
            conv3 = conv_repo.create(title="Third")

        response = client.get("/api/v1/conversations")
        assert response.status_code == 200

        data = response.json()
        assert len(data["data"]) == 3
        # Most recent first
        assert data["data"][0]["title"] == "Third"
        assert data["data"][1]["title"] == "Second"
        assert data["data"][2]["title"] == "First"

    def test_pagination_limit(self, client, temp_db):
        """Should limit number of results with limit parameter."""
        engine = get_engine()
        with Session(engine) as session:
            conv_repo = ConversationRepository(session)
            for i in range(5):
                conv_repo.create(title=f"Conv {i}")

        response = client.get("/api/v1/conversations?limit=2")
        assert response.status_code == 200

        data = response.json()
        assert len(data["data"]) == 2
        assert data["meta"]["total"] == 5
        assert data["meta"]["limit"] == 2

    def test_pagination_offset(self, client, temp_db):
        """Should skip results with offset parameter."""
        import time

        engine = get_engine()
        with Session(engine) as session:
            conv_repo = ConversationRepository(session)
            for i in range(5):
                conv_repo.create(title=f"Conv {i}")
                time.sleep(0.01)

        response = client.get("/api/v1/conversations?limit=2&offset=2")
        assert response.status_code == 200

        data = response.json()
        assert len(data["data"]) == 2
        assert data["meta"]["offset"] == 2
        # Should get Conv 2 and Conv 1 (skipping Conv 4, Conv 3)
        assert data["data"][0]["title"] == "Conv 2"
        assert data["data"][1]["title"] == "Conv 1"

    def test_limit_validation_max(self, client):
        """Should reject limit greater than 100."""
        response = client.get("/api/v1/conversations?limit=101")
        assert response.status_code == 422  # Validation error

    def test_limit_validation_min(self, client):
        """Should reject limit less than 1."""
        response = client.get("/api/v1/conversations?limit=0")
        assert response.status_code == 422  # Validation error

    def test_offset_validation_negative(self, client):
        """Should reject negative offset."""
        response = client.get("/api/v1/conversations?offset=-1")
        assert response.status_code == 422  # Validation error

    def test_conversation_fields_present(self, client, sample_conversation):
        """Should include id, title, created_at, updated_at for each conversation."""
        response = client.get("/api/v1/conversations")
        assert response.status_code == 200

        data = response.json()
        conv = data["data"][0]
        assert "id" in conv
        assert "title" in conv
        assert "created_at" in conv
        assert "updated_at" in conv

    def test_offset_exceeds_total(self, client, sample_conversation):
        """Should return empty list when offset exceeds total count."""
        response = client.get("/api/v1/conversations?offset=100")
        assert response.status_code == 200

        data = response.json()
        assert data["data"] == []
        assert data["meta"]["total"] == 1  # sample_conversation exists
        assert data["meta"]["offset"] == 100
