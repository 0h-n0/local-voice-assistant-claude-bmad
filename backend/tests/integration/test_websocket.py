"""Integration tests for WebSocket endpoint"""

import json

import pytest
from fastapi.testclient import TestClient

from voice_assistant.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestWebSocketConnection:
    """Tests for WebSocket connection lifecycle."""

    def test_websocket_connect_succeeds(self, client: TestClient):
        """Test WebSocket connection establishment."""
        with client.websocket_connect("/api/v1/ws/chat") as websocket:
            assert websocket is not None

    def test_websocket_echo_text(self, client: TestClient):
        """Test WebSocket echo functionality with text message."""
        with client.websocket_connect("/api/v1/ws/chat") as websocket:
            test_message = "hello"
            websocket.send_text(test_message)
            response = websocket.receive_text()
            assert response == test_message

    def test_websocket_echo_json(self, client: TestClient):
        """Test WebSocket echo with JSON message."""
        with client.websocket_connect("/api/v1/ws/chat") as websocket:
            test_data = {"type": "test", "payload": "data"}
            websocket.send_text(json.dumps(test_data))
            response = websocket.receive_text()
            assert json.loads(response) == test_data

    def test_websocket_multiple_messages(self, client: TestClient):
        """Test multiple message exchanges in single connection."""
        with client.websocket_connect("/api/v1/ws/chat") as websocket:
            messages = ["first", "second", "third"]
            for msg in messages:
                websocket.send_text(msg)
                response = websocket.receive_text()
                assert response == msg

    def test_websocket_disconnect_clean(self, client: TestClient):
        """Test clean WebSocket disconnection."""
        # Use a flag to verify connection was established then closed
        connection_established = False

        with client.websocket_connect("/api/v1/ws/chat") as websocket:
            connection_established = True
            # Send a message to verify connection is working
            websocket.send_text("ping")
            response = websocket.receive_text()
            assert response == "ping"

        # After context manager exits, connection should be closed
        assert connection_established

    def test_websocket_handles_empty_message(self, client: TestClient):
        """Test WebSocket handles empty string message."""
        with client.websocket_connect("/api/v1/ws/chat") as websocket:
            websocket.send_text("")
            response = websocket.receive_text()
            assert response == ""

    def test_websocket_handles_unicode(self, client: TestClient):
        """Test WebSocket handles Japanese unicode correctly."""
        with client.websocket_connect("/api/v1/ws/chat") as websocket:
            test_message = "こんにちは、音声アシスタントです"
            websocket.send_text(test_message)
            response = websocket.receive_text()
            assert response == test_message
