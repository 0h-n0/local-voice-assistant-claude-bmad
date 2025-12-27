"""TTS (Text-to-Speech) module for voice assistant."""

from voice_assistant.tts.base import TTS_SAMPLE_RATE, BaseTTS, TTSResult
from voice_assistant.tts.sentence_buffer import SentenceBuffer
from voice_assistant.tts.style_bert_vits2 import StyleBertVits2TTS, get_tts_device

__all__ = [
    "TTS_SAMPLE_RATE",
    "BaseTTS",
    "TTSResult",
    "SentenceBuffer",
    "StyleBertVits2TTS",
    "get_tts_device",
]
