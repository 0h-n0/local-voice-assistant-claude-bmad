"""WebSocket endpoint for real-time voice chat"""

import json
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from voice_assistant.core.logging import get_logger
from voice_assistant.stt import ReazonSpeechSTT, get_stt_device

router = APIRouter()
logger = get_logger(__name__)

# Global STT service instance (lazy loaded)
_stt_service: Optional[ReazonSpeechSTT] = None


def get_stt_service() -> ReazonSpeechSTT:
    """Get or create the global STT service instance."""
    global _stt_service
    if _stt_service is None:
        device = get_stt_device()
        logger.info("initializing_stt_service", device=device)
        _stt_service = ReazonSpeechSTT(device=device)
    return _stt_service


class AudioBuffer:
    """Buffer for accumulating audio chunks from VAD."""

    def __init__(self) -> None:
        self.chunks: list[bytes] = []
        self.sample_rate: int = 16000

    def add_chunk(self, data: bytes, sample_rate: int = 16000) -> None:
        self.chunks.append(data)
        self.sample_rate = sample_rate

    def get_audio(self) -> bytes:
        return b"".join(self.chunks)

    def clear(self) -> None:
        self.chunks = []

    def has_audio(self) -> bool:
        return len(self.chunks) > 0


async def handle_vad_end(
    websocket: WebSocket,
    audio_buffer: AudioBuffer,
    client_info: str,
) -> None:
    """Handle vad.end event by running STT and sending results.

    Args:
        websocket: The WebSocket connection.
        audio_buffer: Buffer containing accumulated audio data.
        client_info: Client identification string for logging.
    """
    if not audio_buffer.has_audio():
        logger.debug("vad_end_no_audio", client=client_info)
        return

    audio_data = audio_buffer.get_audio()
    sample_rate = audio_buffer.sample_rate

    logger.info(
        "stt_processing_start",
        client=client_info,
        audio_bytes=len(audio_data),
        sample_rate=sample_rate,
    )

    try:
        stt_service = get_stt_service()
        result = await stt_service.transcribe(audio_data, sample_rate)

        # Send stt.final event (stt.partial is not supported by ReazonSpeech)
        await websocket.send_json(
            {
                "type": "stt.final",
                "text": result.text,
                "latency_ms": round(result.latency_ms, 2),
            }
        )

        logger.info(
            "stt_final_sent",
            client=client_info,
            text_length=len(result.text),
            latency_ms=round(result.latency_ms, 2),
        )

    except Exception as e:
        logger.error(
            "stt_processing_error",
            client=client_info,
            error=str(e),
        )
        # Send error event to client
        await websocket.send_json(
            {
                "type": "error",
                "code": "STT_ERROR",
                "message": "音声認識に失敗しました",
            }
        )

    finally:
        audio_buffer.clear()


async def handle_text_message(
    websocket: WebSocket,
    data: str,
    audio_buffer: AudioBuffer,
    client_info: str,
) -> None:
    """Handle text (JSON) messages from client."""
    try:
        event = json.loads(data)
        event_type = event.get("type", "unknown")

        if event_type == "vad.start":
            logger.info(
                "vad_start_received",
                client=client_info,
                timestamp=event.get("timestamp"),
            )
            audio_buffer.clear()

        elif event_type == "vad.end":
            logger.info(
                "vad_end_received",
                client=client_info,
                timestamp=event.get("timestamp"),
                audio_chunks=len(audio_buffer.chunks),
            )
            # Process audio with STT
            await handle_vad_end(websocket, audio_buffer, client_info)

        elif event_type == "cancel":
            logger.info("cancel_received", client=client_info)
            audio_buffer.clear()

        else:
            logger.debug("unknown_event", client=client_info, event_type=event_type)

    except json.JSONDecodeError:
        logger.warning("invalid_json", client=client_info, data=data[:100])


async def handle_binary_message(
    data: bytes,
    audio_buffer: AudioBuffer,
    client_info: str,
) -> None:
    """Handle binary (audio) messages from client.

    Protocol: first 4 bytes = header length, then JSON header, then audio data.
    """
    if len(data) < 4:
        logger.warning("binary_too_short", client=client_info, length=len(data))
        return

    # Parse header length (first 4 bytes as uint32)
    header_length = int.from_bytes(data[:4], byteorder="little")

    if len(data) < 4 + header_length:
        logger.warning(
            "binary_header_truncated",
            client=client_info,
            expected=4 + header_length,
            actual=len(data),
        )
        return

    # Parse JSON header
    try:
        header_json = data[4 : 4 + header_length].decode("utf-8")
        header = json.loads(header_json)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.warning("binary_header_parse_error", client=client_info, error=str(e))
        return

    event_type = header.get("type", "unknown")
    sample_rate = header.get("sampleRate", 16000)

    if event_type == "vad.audio":
        audio_data = data[4 + header_length :]
        audio_buffer.add_chunk(audio_data, sample_rate)
        logger.debug(
            "vad_audio_received",
            client=client_info,
            chunk_size=len(audio_data),
            sample_rate=sample_rate,
        )
    else:
        logger.debug(
            "unknown_binary_event",
            client=client_info,
            event_type=event_type,
        )


@router.websocket("/api/v1/ws/chat")
async def websocket_chat(websocket: WebSocket) -> None:
    """WebSocket endpoint for voice chat.

    Handles real-time bidirectional communication between frontend and backend.
    Supports both text (JSON events) and binary (audio data) messages.

    Args:
        websocket: The WebSocket connection.
    """
    await websocket.accept()
    client_info = str(websocket.client) if websocket.client else "unknown"
    logger.info("websocket_connected", client=client_info)

    audio_buffer = AudioBuffer()

    try:
        while True:
            # Receive message (can be text or binary)
            message = await websocket.receive()

            if message["type"] == "websocket.receive":
                if "text" in message:
                    await handle_text_message(
                        websocket,
                        message["text"],
                        audio_buffer,
                        client_info,
                    )
                elif "bytes" in message:
                    await handle_binary_message(
                        message["bytes"],
                        audio_buffer,
                        client_info,
                    )

            elif message["type"] == "websocket.disconnect":
                break

    except WebSocketDisconnect:
        logger.info("websocket_disconnected", client=client_info)
