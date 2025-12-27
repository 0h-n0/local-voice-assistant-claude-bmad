"""Base class for TTS (Text-to-Speech) services."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

# Default sample rate for TTS audio output
TTS_SAMPLE_RATE = 44100


@dataclass
class TTSResult:
    """Result of a TTS synthesis operation."""

    audio: bytes  # PCM16 audio data
    sample_rate: int  # Sample rate in Hz
    latency_ms: float  # Processing time in milliseconds


class BaseTTS(ABC):
    """Abstract base class for TTS services."""

    @abstractmethod
    async def synthesize(self, text: str) -> TTSResult:
        """Synthesize text to speech.

        Args:
            text: Text to synthesize.

        Returns:
            TTSResult with audio data and latency information.
        """
        pass
