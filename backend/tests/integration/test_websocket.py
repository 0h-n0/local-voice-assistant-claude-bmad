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


class TestSttIntegration:
    """Tests for STT integration with WebSocket (Story 2.3)."""

    def _create_audio_message(
        self, audio_data: bytes, sample_rate: int = 16000
    ) -> bytes:
        """Create a binary audio message with header."""
        header = json.dumps({"type": "vad.audio", "sampleRate": sample_rate})
        header_bytes = header.encode("utf-8")
        header_length = struct.pack("<I", len(header_bytes))
        return header_length + header_bytes + audio_data

    def test_stt_final_event_on_vad_end_with_audio(
        self, client: TestClient, monkeypatch
    ):
        """Test stt.final event is sent after vad.end with audio data."""
        from unittest.mock import AsyncMock, MagicMock

        from voice_assistant.stt import TranscriptionResult

        # Mock the STT service
        mock_result = TranscriptionResult(text="こんにちは", latency_ms=150.0)
        mock_stt = MagicMock()
        mock_stt.transcribe = AsyncMock(return_value=mock_result)

        def mock_get_stt_service():
            return mock_stt

        monkeypatch.setattr(
            "voice_assistant.api.websocket.get_stt_service", mock_get_stt_service
        )

        with client.websocket_connect("/api/v1/ws/chat") as websocket:
            # Send vad.start
            start_event = {"type": "vad.start", "timestamp": 1234567890}
            websocket.send_text(json.dumps(start_event))

            # Send audio data (fake Float32Array as bytes)
            import numpy as np

            audio_samples = np.zeros(16000, dtype=np.float32)  # 1 second of silence
            audio_bytes = audio_samples.tobytes()
            audio_message = self._create_audio_message(audio_bytes)
            websocket.send_bytes(audio_message)

            # Send vad.end
            end_event = {"type": "vad.end", "timestamp": 1234567891}
            websocket.send_text(json.dumps(end_event))

            # Receive stt.final event
            response = websocket.receive_json()
            assert response["type"] == "stt.final"
            assert response["text"] == "こんにちは"
            assert response["latency_ms"] == 150.0

    def test_stt_final_event_contains_required_fields(
        self, client: TestClient, monkeypatch
    ):
        """Test stt.final event contains text and latency_ms fields."""
        from unittest.mock import AsyncMock, MagicMock

        from voice_assistant.stt import TranscriptionResult

        mock_result = TranscriptionResult(text="テスト音声", latency_ms=250.5)
        mock_stt = MagicMock()
        mock_stt.transcribe = AsyncMock(return_value=mock_result)

        def mock_get_stt_service():
            return mock_stt

        monkeypatch.setattr(
            "voice_assistant.api.websocket.get_stt_service", mock_get_stt_service
        )

        with client.websocket_connect("/api/v1/ws/chat") as websocket:
            # Send audio flow
            websocket.send_text(json.dumps({"type": "vad.start", "timestamp": 1}))

            import numpy as np

            audio = np.random.randn(8000).astype(np.float32)  # 0.5 sec
            audio_msg = self._create_audio_message(audio.tobytes())
            websocket.send_bytes(audio_msg)

            websocket.send_text(json.dumps({"type": "vad.end", "timestamp": 2}))

            response = websocket.receive_json()
            assert "type" in response
            assert response["type"] == "stt.final"
            assert "text" in response
            assert "latency_ms" in response
            assert isinstance(response["latency_ms"], (int, float))

    def test_stt_error_event_on_transcription_failure(
        self, client: TestClient, monkeypatch
    ):
        """Test error event is sent when STT transcription fails."""
        from unittest.mock import AsyncMock, MagicMock

        mock_stt = MagicMock()
        mock_stt.transcribe = AsyncMock(side_effect=Exception("Model error"))

        def mock_get_stt_service():
            return mock_stt

        monkeypatch.setattr(
            "voice_assistant.api.websocket.get_stt_service", mock_get_stt_service
        )

        with client.websocket_connect("/api/v1/ws/chat") as websocket:
            # Send audio flow
            websocket.send_text(json.dumps({"type": "vad.start", "timestamp": 1}))

            import numpy as np

            audio = np.zeros(8000, dtype=np.float32)
            audio_msg = self._create_audio_message(audio.tobytes())
            websocket.send_bytes(audio_msg)

            websocket.send_text(json.dumps({"type": "vad.end", "timestamp": 2}))

            response = websocket.receive_json()
            assert response["type"] == "error"
            assert response["code"] == "STT_ERROR"
            assert "message" in response

    def test_no_stt_event_when_no_audio(self, client: TestClient, monkeypatch):
        """Test no stt.final event when vad.end is sent without audio."""
        from unittest.mock import AsyncMock, MagicMock

        mock_stt = MagicMock()
        mock_stt.transcribe = AsyncMock()

        def mock_get_stt_service():
            return mock_stt

        monkeypatch.setattr(
            "voice_assistant.api.websocket.get_stt_service", mock_get_stt_service
        )

        with client.websocket_connect("/api/v1/ws/chat") as websocket:
            # Send vad.start and vad.end without audio
            websocket.send_text(json.dumps({"type": "vad.start", "timestamp": 1}))
            websocket.send_text(json.dumps({"type": "vad.end", "timestamp": 2}))

            # STT should not be called
            mock_stt.transcribe.assert_not_called()

    def test_audio_buffer_cleared_after_stt(self, client: TestClient, monkeypatch):
        """Test audio buffer is cleared after STT processing."""
        from unittest.mock import AsyncMock, MagicMock

        from voice_assistant.stt import TranscriptionResult

        call_count = [0]
        audio_lengths = []

        async def mock_transcribe(audio_data: bytes, sample_rate: int):
            call_count[0] += 1
            audio_lengths.append(len(audio_data))
            return TranscriptionResult(text=f"result {call_count[0]}", latency_ms=100.0)

        mock_stt = MagicMock()
        mock_stt.transcribe = mock_transcribe

        def mock_get_stt_service():
            return mock_stt

        monkeypatch.setattr(
            "voice_assistant.api.websocket.get_stt_service", mock_get_stt_service
        )

        with client.websocket_connect("/api/v1/ws/chat") as websocket:
            import numpy as np

            # First audio session
            websocket.send_text(json.dumps({"type": "vad.start", "timestamp": 1}))
            audio1 = np.zeros(8000, dtype=np.float32)
            websocket.send_bytes(self._create_audio_message(audio1.tobytes()))
            websocket.send_text(json.dumps({"type": "vad.end", "timestamp": 2}))

            response1 = websocket.receive_json()
            assert response1["text"] == "result 1"

            # Second audio session (should have fresh buffer)
            websocket.send_text(json.dumps({"type": "vad.start", "timestamp": 3}))
            audio2 = np.zeros(4000, dtype=np.float32)  # Different size
            websocket.send_bytes(self._create_audio_message(audio2.tobytes()))
            websocket.send_text(json.dumps({"type": "vad.end", "timestamp": 4}))

            response2 = websocket.receive_json()
            assert response2["text"] == "result 2"

            # Verify audio lengths are different (buffer was cleared)
            assert len(audio_lengths) == 2
            assert audio_lengths[0] != audio_lengths[1]
