"""Unit tests for STT module."""

import numpy as np
import pytest

from voice_assistant.stt import get_stt_device
from voice_assistant.stt.base import TranscriptionResult


class TestGetSttDevice:
    """Tests for get_stt_device function."""

    def test_returns_string(self) -> None:
        """Test that get_stt_device returns a string."""
        device = get_stt_device()
        assert isinstance(device, str)

    def test_returns_valid_device(self) -> None:
        """Test that get_stt_device returns a valid device name."""
        device = get_stt_device()
        assert device in ("cuda", "cpu")


class TestTranscriptionResult:
    """Tests for TranscriptionResult dataclass."""

    def test_create_result(self) -> None:
        """Test creating a TranscriptionResult."""
        result = TranscriptionResult(text="hello", latency_ms=100.5)
        assert result.text == "hello"
        assert result.latency_ms == 100.5

    def test_empty_text(self) -> None:
        """Test creating a result with empty text."""
        result = TranscriptionResult(text="", latency_ms=50.0)
        assert result.text == ""
        assert result.latency_ms == 50.0


class TestReazonSpeechSTT:
    """Tests for ReazonSpeechSTT class (without model loading)."""

    def test_import_reazon_speech_stt(self) -> None:
        """Test that ReazonSpeechSTT can be imported."""
        from voice_assistant.stt import ReazonSpeechSTT

        assert ReazonSpeechSTT is not None

    def test_init_with_device(self) -> None:
        """Test initializing with a specific device."""
        from voice_assistant.stt import ReazonSpeechSTT

        stt = ReazonSpeechSTT(device="cpu")
        assert stt.device == "cpu"
        assert not stt.is_model_loaded

    def test_init_with_auto_device(self) -> None:
        """Test initializing with automatic device detection."""
        from voice_assistant.stt import ReazonSpeechSTT

        stt = ReazonSpeechSTT()
        assert stt.device in ("cuda", "cpu")
        assert not stt.is_model_loaded


class TestAudioDataConversion:
    """Tests for audio data conversion utilities."""

    def test_float32_array_to_numpy(self) -> None:
        """Test converting Float32Array bytes to numpy array."""
        original = np.array([0.1, 0.2, -0.3, 0.4], dtype=np.float32)
        audio_bytes = original.tobytes()

        reconstructed = np.frombuffer(audio_bytes, dtype=np.float32)
        np.testing.assert_array_almost_equal(original, reconstructed)

    def test_empty_audio_bytes(self) -> None:
        """Test handling empty audio bytes."""
        empty_bytes = b""
        reconstructed = np.frombuffer(empty_bytes, dtype=np.float32)
        assert len(reconstructed) == 0


class TestReazonSpeechSTTTranscribe:
    """Tests for ReazonSpeechSTT.transcribe method edge cases."""

    @pytest.mark.asyncio
    async def test_transcribe_empty_audio_returns_empty_text(self) -> None:
        """Test that empty audio bytes returns empty TranscriptionResult.

        Empty audio is handled before model loading, so no mock needed.
        """
        from voice_assistant.stt import ReazonSpeechSTT

        stt = ReazonSpeechSTT(device="cpu")
        # Empty audio should return immediately without loading model
        result = await stt.transcribe(b"", sample_rate=16000)

        assert result.text == ""
        assert result.latency_ms == 0.0
        # Model should NOT be loaded for empty audio
        assert not stt.is_model_loaded

    def test_audio_data_various_sample_rates(self) -> None:
        """Test audio data conversion with different sample rates."""
        # Valid sample rates for ReazonSpeech: 16000 Hz
        audio = np.zeros(8000, dtype=np.float32)  # 0.5 sec at 16kHz
        audio_bytes = audio.tobytes()

        # Verify bytes conversion is correct
        reconstructed = np.frombuffer(audio_bytes, dtype=np.float32)
        assert len(reconstructed) == 8000

    def test_audio_data_large_array(self) -> None:
        """Test handling of larger audio arrays (simulating longer speech)."""
        # 10 seconds of audio at 16kHz
        audio = np.random.randn(160000).astype(np.float32)
        audio_bytes = audio.tobytes()

        reconstructed = np.frombuffer(audio_bytes, dtype=np.float32)
        assert len(reconstructed) == 160000
        np.testing.assert_array_equal(audio, reconstructed)

    def test_audio_normalization_range(self) -> None:
        """Test audio data within expected range [-1.0, 1.0]."""
        # Audio should typically be normalized
        audio = np.array([-1.0, -0.5, 0.0, 0.5, 1.0], dtype=np.float32)
        audio_bytes = audio.tobytes()

        reconstructed = np.frombuffer(audio_bytes, dtype=np.float32)
        assert reconstructed.min() >= -1.0
        assert reconstructed.max() <= 1.0
