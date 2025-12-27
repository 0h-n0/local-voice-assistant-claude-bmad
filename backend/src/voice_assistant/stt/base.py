"""Base class for STT (Speech-to-Text) services."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TranscriptionResult:
    """Result of a transcription operation."""

    text: str
    latency_ms: float


class BaseSTT(ABC):
    """Abstract base class for STT services."""

    @abstractmethod
    async def transcribe(
        self, audio_data: bytes, sample_rate: int
    ) -> TranscriptionResult:
        """Transcribe audio data to text.

        Args:
            audio_data: Raw audio bytes (Float32Array from frontend).
            sample_rate: Sample rate of the audio in Hz.

        Returns:
            TranscriptionResult with text and latency information.
        """
        pass
