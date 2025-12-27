"""Style-BERT-VITS2 TTS implementation."""

import asyncio
import os
import threading
import time
from pathlib import Path

import numpy as np
import torch

from voice_assistant.core.logging import get_logger
from voice_assistant.tts.base import TTS_SAMPLE_RATE, BaseTTS, TTSResult

logger = get_logger(__name__)

# Default model paths (can be overridden via environment variables)
DEFAULT_MODEL_DIR = Path(__file__).parent.parent.parent.parent.parent / "models" / "tts"


def get_tts_device() -> str:
    """Get the device for TTS inference.

    Returns:
        'cuda' if CUDA is available, otherwise 'cpu'.
    """
    return "cuda" if torch.cuda.is_available() else "cpu"


class StyleBertVits2TTS(BaseTTS):
    """TTS service using Style-BERT-VITS2.

    Provides Japanese text-to-speech synthesis using the
    Style-BERT-VITS2 model with lazy loading and thread-safe
    initialization.

    Model files must be downloaded separately and placed in the models/tts directory.
    Required files:
    - config.json
    - *.safetensors (model weights)
    - style_vectors.npy
    """

    _instance_lock = threading.Lock()

    def __init__(
        self,
        device: str = "auto",
        model_dir: str | Path | None = None,
    ) -> None:
        """Initialize the TTS service.

        Args:
            device: Device to use ('auto', 'cuda', or 'cpu').
                   'auto' will use CUDA if available.
            model_dir: Directory containing model files.
                      Defaults to models/tts or TTS_MODEL_DIR env var.
        """
        self.device = get_tts_device() if device == "auto" else device
        self._model = None
        self._model_lock = threading.Lock()
        self._model_available = True

        # Resolve model directory
        if model_dir:
            self._model_dir = Path(model_dir)
        else:
            self._model_dir = Path(
                os.getenv("TTS_MODEL_DIR", str(DEFAULT_MODEL_DIR))
            )

    def _find_model_files(self) -> tuple[Path, Path, Path] | None:
        """Find model files in the model directory.

        Returns:
            Tuple of (model_path, config_path, style_vec_path) or None if not found.
        """
        if not self._model_dir.exists():
            logger.warning(
                "tts_model_dir_not_found",
                model_dir=str(self._model_dir),
            )
            return None

        # Find config.json
        config_path = self._model_dir / "config.json"
        if not config_path.exists():
            logger.warning(
                "tts_config_not_found",
                expected_path=str(config_path),
            )
            return None

        # Find .safetensors file
        safetensors = list(self._model_dir.glob("*.safetensors"))
        if not safetensors:
            logger.warning(
                "tts_model_not_found",
                model_dir=str(self._model_dir),
            )
            return None
        model_path = safetensors[0]

        # Find style_vectors.npy
        style_vec_path = self._model_dir / "style_vectors.npy"
        if not style_vec_path.exists():
            logger.warning(
                "tts_style_vectors_not_found",
                expected_path=str(style_vec_path),
            )
            return None

        return model_path, config_path, style_vec_path

    def _load_model(self):
        """Load the TTS model (thread-safe, lazy loading).

        Returns:
            The loaded TTS model, or None if model is unavailable.
        """
        if self._model is None and self._model_available:
            with self._model_lock:
                # Double-check locking
                if self._model is None and self._model_available:
                    model_files = self._find_model_files()
                    if model_files is None:
                        self._model_available = False
                        logger.warning(
                            "tts_model_unavailable",
                            message="TTS model files not found. TTS will be disabled.",
                        )
                        return None

                    model_path, config_path, style_vec_path = model_files

                    logger.info(
                        "loading_tts_model",
                        device=self.device,
                        model_path=str(model_path),
                    )

                    try:
                        # Import here to avoid slow startup
                        from style_bert_vits2.constants import Languages
                        from style_bert_vits2.nlp import bert_models
                        from style_bert_vits2.tts_model import TTSModel

                        # Load BERT models for Japanese
                        bert_models.load_model(
                            Languages.JP,
                            "ku-nlp/deberta-v2-large-japanese-char-wwm",
                        )
                        bert_models.load_tokenizer(
                            Languages.JP,
                            "ku-nlp/deberta-v2-large-japanese-char-wwm",
                        )

                        # Initialize and load the model
                        self._model = TTSModel(
                            model_path=model_path,
                            config_path=config_path,
                            style_vec_path=style_vec_path,
                            device=self.device,
                        )
                        self._model.load()

                        logger.info(
                            "tts_model_loaded",
                            device=self.device,
                        )
                    except Exception as e:
                        self._model_available = False
                        logger.error(
                            "tts_model_load_error",
                            error=str(e),
                        )
                        return None

        return self._model

    async def synthesize(self, text: str) -> TTSResult:
        """Synthesize text to speech.

        Args:
            text: Text to synthesize.

        Returns:
            TTSResult with PCM16 audio data and latency.
            Returns empty audio if model is unavailable.
        """
        if not text or not text.strip():
            return TTSResult(audio=b"", sample_rate=TTS_SAMPLE_RATE, latency_ms=0.0)

        start_time = time.perf_counter()

        # Load model (lazy)
        model = self._load_model()
        if model is None:
            # Model not available, return empty result with warning
            logger.debug(
                "tts_skipped_model_unavailable",
                text_length=len(text),
            )
            return TTSResult(audio=b"", sample_rate=TTS_SAMPLE_RATE, latency_ms=0.0)

        # Run inference in thread pool (blocking operation)
        sample_rate, audio = await asyncio.to_thread(
            model.infer,
            text=text,
        )

        # Convert float32 audio (-1.0 to 1.0) to PCM16 bytes
        audio_int16 = (audio * 32767).astype(np.int16)
        audio_bytes = audio_int16.tobytes()

        latency_ms = (time.perf_counter() - start_time) * 1000

        logger.debug(
            "tts_synthesis_complete",
            text_length=len(text),
            audio_length=len(audio_bytes),
            sample_rate=sample_rate,
            latency_ms=round(latency_ms, 2),
        )

        return TTSResult(
            audio=audio_bytes,
            sample_rate=sample_rate,
            latency_ms=latency_ms,
        )
