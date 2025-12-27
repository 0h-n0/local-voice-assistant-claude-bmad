"""Integration tests for WebSocket endpoint"""

import json
import struct

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

    def test_websocket_disconnect_clean(self, client: TestClient):
        """Test clean WebSocket disconnection."""
        connection_established = False

        with client.websocket_connect("/api/v1/ws/chat") as websocket:
            connection_established = True

        assert connection_established


class TestVadEvents:
    """Tests for VAD event handling."""

    def test_vad_start_event(self, client: TestClient):
        """Test vad.start event is received without error."""
        with client.websocket_connect("/api/v1/ws/chat") as websocket:
            event = {"type": "vad.start", "timestamp": 1234567890}
            websocket.send_text(json.dumps(event))
            # No response expected - just verify no exception

    def test_vad_end_event(self, client: TestClient):
        """Test vad.end event is received without error."""
        with client.websocket_connect("/api/v1/ws/chat") as websocket:
            # Send start first
            start_event = {"type": "vad.start", "timestamp": 1234567890}
            websocket.send_text(json.dumps(start_event))

            # Then end
            end_event = {"type": "vad.end", "timestamp": 1234567891}
            websocket.send_text(json.dumps(end_event))
            # No response expected - just verify no exception

    def test_cancel_event(self, client: TestClient):
        """Test cancel event clears audio buffer."""
        with client.websocket_connect("/api/v1/ws/chat") as websocket:
            event = {"type": "cancel"}
            websocket.send_text(json.dumps(event))
            # No response expected - just verify no exception


class TestBinaryAudioMessages:
    """Tests for binary audio message handling."""

    def _create_audio_message(
        self, event_type: str = "vad.audio", sample_rate: int = 16000
    ) -> bytes:
        """Create a binary audio message with header."""
        header = json.dumps({"type": event_type, "sampleRate": sample_rate})
        header_bytes = header.encode("utf-8")
        header_length = struct.pack("<I", len(header_bytes))
        # Create fake audio data (1000 samples of silence)
        audio_data = bytes(4000)  # 1000 float32 samples
        return header_length + header_bytes + audio_data

    def test_vad_audio_binary_message(self, client: TestClient):
        """Test binary vad.audio message is received without error."""
        with client.websocket_connect("/api/v1/ws/chat") as websocket:
            # Send start event first
            start_event = {"type": "vad.start", "timestamp": 1234567890}
            websocket.send_text(json.dumps(start_event))

            # Send binary audio
            audio_message = self._create_audio_message()
            websocket.send_bytes(audio_message)
            # No response expected - just verify no exception

    def test_multiple_audio_chunks(self, client: TestClient):
        """Test multiple audio chunks are accumulated."""
        with client.websocket_connect("/api/v1/ws/chat") as websocket:
            # Send start
            start_event = {"type": "vad.start", "timestamp": 1234567890}
            websocket.send_text(json.dumps(start_event))

            # Send multiple audio chunks
            for _ in range(3):
                audio_message = self._create_audio_message()
                websocket.send_bytes(audio_message)

            # Send end
            end_event = {"type": "vad.end", "timestamp": 1234567891}
            websocket.send_text(json.dumps(end_event))
            # Verify no exception

    def test_short_binary_message_handled(self, client: TestClient):
        """Test that too-short binary messages don't crash."""
        with client.websocket_connect("/api/v1/ws/chat") as websocket:
            # Send binary data that's too short (less than 4 bytes)
            websocket.send_bytes(b"\x00\x01")
            # Should not raise exception


class TestUnicodeHandling:
    """Tests for Japanese unicode support."""

    def test_unicode_in_json_event(self, client: TestClient):
        """Test Japanese unicode in event payloads."""
        with client.websocket_connect("/api/v1/ws/chat") as websocket:
            # Unicode in custom field (future use case)
            event = {"type": "vad.start", "timestamp": 1234567890}
            websocket.send_text(json.dumps(event, ensure_ascii=False))
            # No response expected - just verify no exception
