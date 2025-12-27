"""ReazonSpeech NeMo v2 STT implementation."""

import asyncio
import time

# Workaround for ml_dtypes compatibility issue (see Issue #16)
# nemo-toolkit expects float4/float8 types which are only in ml_dtypes >= 0.5.0
# but reazonspeech requires numpy < 2 which conflicts with ml_dtypes >= 0.5.0
# https://github.com/0h-n0/local-voice-assistant-claude-bmad/issues/16
import ml_dtypes
_missing_types = [
    'float4_e2m1fn',
    'float8_e8m0fnu',
    'float8_e4m3',
    'float8_e4m3fn',
    'float8_e4m3fnuz',
    'float8_e4m3b11fnuz',
    'float8_e5m2',
    'float8_e5m2fnuz',
]
for _dtype in _missing_types:
    if not hasattr(ml_dtypes, _dtype):
        setattr(ml_dtypes, _dtype, type(_dtype, (), {}))

import numpy as np
import torch

from voice_assistant.core.logging import get_logger
from voice_assistant.stt.base import BaseSTT, TranscriptionResult

logger = get_logger(__name__)


def get_stt_device() -> str:
    """Determine the best device for STT processing.

    Returns:
        "cuda" if GPU is available, "cpu" otherwise.
    """
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


class ReazonSpeechSTT(BaseSTT):
    """ReazonSpeech NeMo v2 STT service.

    This service uses ReazonSpeech NeMo v2 model for Japanese speech recognition.
    The model is lazily loaded on first transcription request.
    """

    def __init__(self, device: str | None = None):
        """Initialize the STT service.

        Args:
            device: Device to use for inference ("cuda" or "cpu").
                   If None, automatically detects the best device.
        """
        self.device = device or get_stt_device()
        self._model = None
        self._model_lock = asyncio.Lock()

    @property
    def is_model_loaded(self) -> bool:
        """Check if the model is loaded."""
        return self._model is not None

    async def _ensure_model_loaded(self) -> None:
        """Ensure the model is loaded (lazy loading with lock)."""
        if self._model is not None:
            return

        async with self._model_lock:
            if self._model is not None:
                return

            logger.info("loading_reazon_speech_model", device=self.device)
            start_time = time.perf_counter()

            from reazonspeech.nemo.asr import load_model

            self._model = await asyncio.to_thread(load_model, device=self.device)

            load_time_ms = (time.perf_counter() - start_time) * 1000
            logger.info(
                "reazon_speech_model_loaded",
                device=self.device,
                load_time_ms=round(load_time_ms, 2),
            )

    async def transcribe(
        self, audio_data: bytes, sample_rate: int
    ) -> TranscriptionResult:
        """Transcribe audio data to text using ReazonSpeech.

        Args:
            audio_data: Raw audio bytes (Float32Array from frontend).
            sample_rate: Sample rate of the audio in Hz.

        Returns:
            TranscriptionResult with transcribed text and latency.
        """
        # Early return for empty audio - avoid loading model unnecessarily
        audio_array = np.frombuffer(audio_data, dtype=np.float32)
        if len(audio_array) == 0:
            return TranscriptionResult(text="", latency_ms=0.0)

        await self._ensure_model_loaded()

        start_time = time.perf_counter()

        from reazonspeech.nemo.asr import audio_from_numpy, transcribe

        audio = audio_from_numpy(audio_array, sample_rate)

        result = await asyncio.to_thread(transcribe, self._model, audio)

        latency_ms = (time.perf_counter() - start_time) * 1000
        text = result.text if result.text else ""

        logger.info(
            "stt_completed",
            text=text[:50] if text else "",
            text_length=len(text),
            audio_duration_sec=round(len(audio_array) / sample_rate, 2),
            latency_ms=round(latency_ms, 2),
        )

        return TranscriptionResult(text=text, latency_ms=latency_ms)
