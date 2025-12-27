"""STT (Speech-to-Text) module for voice assistant."""

from voice_assistant.stt.base import BaseSTT, TranscriptionResult
from voice_assistant.stt.reazon_speech import ReazonSpeechSTT, get_stt_device

__all__ = [
    "BaseSTT",
    "TranscriptionResult",
    "ReazonSpeechSTT",
    "get_stt_device",
]
