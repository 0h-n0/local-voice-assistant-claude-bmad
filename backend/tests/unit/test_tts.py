"""Unit tests for TTS (Text-to-Speech) module."""

from abc import ABC
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest


class TestTTSResult:
    """Tests for TTSResult dataclass."""

    def test_create_result(self):
        """Test creating a TTSResult with valid data."""
        from voice_assistant.tts.base import TTSResult

        audio = b"\x00\x01\x02\x03"
        result = TTSResult(audio=audio, sample_rate=44100, latency_ms=150.5)

        assert result.audio == audio
        assert result.sample_rate == 44100
        assert result.latency_ms == 150.5

    def test_empty_audio(self):
        """Test creating a TTSResult with empty audio."""
        from voice_assistant.tts.base import TTSResult

        result = TTSResult(audio=b"", sample_rate=44100, latency_ms=0.0)

        assert result.audio == b""
        assert result.sample_rate == 44100


class TestBaseTTS:
    """Tests for BaseTTS abstract class."""

    def test_is_abstract(self):
        """Test that BaseTTS cannot be instantiated directly."""
        from voice_assistant.tts.base import BaseTTS

        assert issubclass(BaseTTS, ABC)
        with pytest.raises(TypeError, match="abstract"):
            BaseTTS()


class TestSentenceBuffer:
    """Tests for SentenceBuffer text splitting."""

    def test_split_by_period(self):
        """Test splitting text by Japanese period."""
        from voice_assistant.tts.sentence_buffer import SentenceBuffer

        buffer = SentenceBuffer()
        sentences = buffer.add("こんにちは。元気ですか。")

        assert len(sentences) == 2
        assert sentences[0] == "こんにちは。"
        assert sentences[1] == "元気ですか。"

    def test_split_by_question_mark(self):
        """Test splitting text by question mark."""
        from voice_assistant.tts.sentence_buffer import SentenceBuffer

        buffer = SentenceBuffer()
        sentences = buffer.add("何ですか？分かりました。")

        assert len(sentences) == 2
        assert sentences[0] == "何ですか？"
        assert sentences[1] == "分かりました。"

    def test_split_by_exclamation(self):
        """Test splitting text by exclamation mark."""
        from voice_assistant.tts.sentence_buffer import SentenceBuffer

        buffer = SentenceBuffer()
        sentences = buffer.add("すごい！よくできました。")

        assert len(sentences) == 2
        assert sentences[0] == "すごい！"
        assert sentences[1] == "よくできました。"

    def test_incomplete_sentence(self):
        """Test that incomplete sentences are buffered."""
        from voice_assistant.tts.sentence_buffer import SentenceBuffer

        buffer = SentenceBuffer()
        sentences = buffer.add("これは")

        assert len(sentences) == 0

        sentences = buffer.add("テストです。")
        assert len(sentences) == 1
        assert sentences[0] == "これはテストです。"

    def test_flush_remaining(self):
        """Test flushing remaining buffered text."""
        from voice_assistant.tts.sentence_buffer import SentenceBuffer

        buffer = SentenceBuffer()
        buffer.add("残りの文")
        remaining = buffer.flush()

        assert remaining == "残りの文"

    def test_flush_empty(self):
        """Test flushing when buffer is empty."""
        from voice_assistant.tts.sentence_buffer import SentenceBuffer

        buffer = SentenceBuffer()
        remaining = buffer.flush()

        assert remaining is None

    def test_split_by_newline(self):
        """Test splitting text by newline."""
        from voice_assistant.tts.sentence_buffer import SentenceBuffer

        buffer = SentenceBuffer()
        sentences = buffer.add("一行目\n二行目")

        assert len(sentences) == 1
        assert sentences[0] == "一行目"

        remaining = buffer.flush()
        assert remaining == "二行目"


class TestStyleBertVits2TTS:
    """Tests for StyleBertVits2TTS implementation."""

    def test_import(self):
        """Test that StyleBertVits2TTS can be imported."""
        from voice_assistant.tts.style_bert_vits2 import StyleBertVits2TTS

        assert StyleBertVits2TTS is not None

    def test_init_with_device_auto(self):
        """Test initialization with auto device detection."""
        from voice_assistant.tts.style_bert_vits2 import StyleBertVits2TTS

        tts = StyleBertVits2TTS(device="auto")
        assert tts.device in ("cuda", "cpu")

    def test_init_with_explicit_device(self):
        """Test initialization with explicit device."""
        from voice_assistant.tts.style_bert_vits2 import StyleBertVits2TTS

        tts = StyleBertVits2TTS(device="cpu")
        assert tts.device == "cpu"

    def test_lazy_model_loading(self):
        """Test that model is not loaded until synthesize is called."""
        from voice_assistant.tts.style_bert_vits2 import StyleBertVits2TTS

        tts = StyleBertVits2TTS(device="cpu")
        assert tts._model is None

    @pytest.mark.asyncio
    async def test_synthesize_returns_tts_result(self):
        """Test that synthesize returns a TTSResult."""
        from voice_assistant.tts.base import TTSResult
        from voice_assistant.tts.style_bert_vits2 import StyleBertVits2TTS

        tts = StyleBertVits2TTS(device="cpu")

        # Mock the model inference
        mock_audio = np.zeros(1000, dtype=np.float32)
        with patch.object(tts, "_load_model") as mock_load:
            mock_model = MagicMock()
            mock_model.infer.return_value = (44100, mock_audio)
            mock_load.return_value = mock_model

            result = await tts.synthesize("テスト")

        assert isinstance(result, TTSResult)
        assert result.sample_rate == 44100
        assert result.latency_ms >= 0
        assert len(result.audio) > 0

    @pytest.mark.asyncio
    async def test_synthesize_converts_to_pcm16(self):
        """Test that audio is converted to PCM16 format."""
        from voice_assistant.tts.style_bert_vits2 import StyleBertVits2TTS

        tts = StyleBertVits2TTS(device="cpu")

        # Create audio with known values
        mock_audio = np.array([0.0, 0.5, -0.5, 1.0, -1.0], dtype=np.float32)
        expected_length = len(mock_audio) * 2  # int16 = 2 bytes per sample

        with patch.object(tts, "_load_model") as mock_load:
            mock_model = MagicMock()
            mock_model.infer.return_value = (44100, mock_audio)
            mock_load.return_value = mock_model

            result = await tts.synthesize("テスト")

        assert len(result.audio) == expected_length

    @pytest.mark.asyncio
    async def test_synthesize_empty_text_returns_empty(self):
        """Test that empty text returns empty audio."""
        from voice_assistant.tts.style_bert_vits2 import StyleBertVits2TTS

        tts = StyleBertVits2TTS(device="cpu")

        result = await tts.synthesize("")

        assert result.audio == b""
        assert result.latency_ms >= 0


class TestGetTTSDevice:
    """Tests for get_tts_device function."""

    def test_returns_string(self):
        """Test that get_tts_device returns a string."""
        from voice_assistant.tts.style_bert_vits2 import get_tts_device

        device = get_tts_device()
        assert isinstance(device, str)

    def test_returns_valid_device(self):
        """Test that get_tts_device returns cuda or cpu."""
        from voice_assistant.tts.style_bert_vits2 import get_tts_device

        device = get_tts_device()
        assert device in ("cuda", "cpu")
