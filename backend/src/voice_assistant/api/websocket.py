"""WebSocket endpoint for real-time voice chat"""

import base64
import json
import os
import threading
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from openai import APIError, AuthenticationError, RateLimitError
from sqlmodel import Session

from voice_assistant.core.logging import get_logger
from voice_assistant.db import (
    ConversationRepository,
    MessageRepository,
    get_engine,
)
from voice_assistant.llm import ConversationContext, OpenAICompatLLM
from voice_assistant.stt import ReazonSpeechSTT, get_stt_device
from voice_assistant.tts import SentenceBuffer, StyleBertVits2TTS, get_tts_device

router = APIRouter()
logger = get_logger(__name__)

# Global STT service instance (lazy loaded, thread-safe)
_stt_service: ReazonSpeechSTT | None = None
_stt_service_lock = threading.Lock()

# Global LLM service instance (lazy loaded, thread-safe)
_llm_service: OpenAICompatLLM | None = None
_llm_service_lock = threading.Lock()

# Global TTS service instance (lazy loaded, thread-safe)
_tts_service: StyleBertVits2TTS | None = None
_tts_service_lock = threading.Lock()


def get_stt_service() -> ReazonSpeechSTT:
    """Get or create the global STT service instance (thread-safe)."""
    global _stt_service
    if _stt_service is None:
        with _stt_service_lock:
            # Double-check locking pattern
            if _stt_service is None:
                device = get_stt_device()
                logger.info("initializing_stt_service", device=device)
                _stt_service = ReazonSpeechSTT(device=device)
    return _stt_service


def get_llm_service() -> OpenAICompatLLM:
    """Get or create the global LLM service instance (thread-safe)."""
    global _llm_service
    if _llm_service is None:
        with _llm_service_lock:
            # Double-check locking pattern
            if _llm_service is None:
                base_url = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
                model = os.getenv("LLM_MODEL", "llama3.2")
                logger.info("initializing_llm_service", base_url=base_url, model=model)
                _llm_service = OpenAICompatLLM(base_url=base_url, model=model)
    return _llm_service


def get_tts_service() -> StyleBertVits2TTS:
    """Get or create the global TTS service instance (thread-safe)."""
    global _tts_service
    if _tts_service is None:
        with _tts_service_lock:
            # Double-check locking pattern
            if _tts_service is None:
                device = get_tts_device()
                logger.info("initializing_tts_service", device=device)
                _tts_service = StyleBertVits2TTS(device=device)
    return _tts_service


async def handle_tts_streaming(
    websocket: WebSocket,
    sentence: str,
    client_info: str,
    e2e_start_time: float | None = None,
    is_first_chunk: bool = False,
) -> float:
    """Process a sentence with TTS and send audio chunks.

    Args:
        websocket: The WebSocket connection.
        sentence: The sentence to synthesize.
        client_info: Client identification string for logging.
        e2e_start_time: Start time for E2E latency measurement (from vad.end).
        is_first_chunk: Whether this is the first TTS chunk (for E2E latency logging).

    Returns:
        The TTS processing latency in milliseconds.
    """
    tts_service = get_tts_service()
    result = await tts_service.synthesize(sentence)

    if result.audio:
        # Base64 encode the audio data for WebSocket transmission
        audio_base64 = base64.b64encode(result.audio).decode("utf-8")

        await websocket.send_json(
            {
                "type": "tts.chunk",
                "audio": audio_base64,
                "sampleRate": result.sample_rate,
                "format": "pcm16",
            }
        )

        # Log E2E latency for first TTS chunk (vad.end → first tts.chunk)
        if is_first_chunk and e2e_start_time is not None:
            e2e_latency_ms = (time.perf_counter() - e2e_start_time) * 1000
            logger.info(
                "e2e_first_chunk_latency",
                client=client_info,
                e2e_ms=round(e2e_latency_ms, 2),
            )

        logger.info(
            "tts_chunk_sent",
            client=client_info,
            text_length=len(sentence),
            audio_bytes=len(result.audio),
            sample_rate=result.sample_rate,
            latency_ms=round(result.latency_ms, 2),
        )

    return result.latency_ms


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


class ConversationSession:
    """Manages conversation persistence for a WebSocket session.

    Handles creating conversations and saving messages to the database.
    """

    def __init__(self) -> None:
        self.conversation_id: str | None = None
        self._last_user_message_id: str | None = None
        self._pending_stt_latency: int | None = None
        self._pending_llm_latency: int | None = None
        self._pending_tts_latency: int | None = None

    def _get_session(self) -> Session:
        """Get a database session."""
        return Session(get_engine())

    def ensure_conversation(self) -> str:
        """Ensure a conversation exists, creating one if needed.

        Returns:
            The conversation ID.
        """
        if self.conversation_id is None:
            with self._get_session() as session:
                repo = ConversationRepository(session)
                conv = repo.create()
                self.conversation_id = conv.id
                logger.info("conversation_created", conversation_id=conv.id)
        return self.conversation_id

    def save_user_message(self, text: str, stt_latency_ms: int) -> str | None:
        """Save a user message to the database.

        Args:
            text: The transcribed text.
            stt_latency_ms: STT latency in milliseconds.

        Returns:
            The message ID if saved, None on error.
        """
        if not text.strip():
            return None

        conv_id = self.ensure_conversation()

        try:
            with self._get_session() as session:
                repo = MessageRepository(session)
                msg = repo.create(
                    conversation_id=conv_id,
                    role="user",
                    content=text,
                    stt_latency_ms=int(stt_latency_ms),
                )
                self._last_user_message_id = msg.id
                logger.debug(
                    "user_message_saved",
                    message_id=msg.id,
                    conversation_id=conv_id,
                )
                return msg.id
        except Exception as e:
            logger.error("save_user_message_error", error=str(e))
            return None

    def save_assistant_message(
        self,
        text: str,
        llm_latency_ms: float,
        tts_latency_ms: float | None = None,
    ) -> str | None:
        """Save an assistant message to the database.

        Args:
            text: The LLM response text.
            llm_latency_ms: LLM latency in milliseconds.
            tts_latency_ms: TTS latency in milliseconds (optional).

        Returns:
            The message ID if saved, None on error.
        """
        if not text.strip():
            return None

        conv_id = self.ensure_conversation()

        try:
            with self._get_session() as session:
                repo = MessageRepository(session)
                msg = repo.create(
                    conversation_id=conv_id,
                    role="assistant",
                    content=text,
                    llm_latency_ms=int(llm_latency_ms),
                    tts_latency_ms=int(tts_latency_ms) if tts_latency_ms else None,
                )
                logger.debug(
                    "assistant_message_saved",
                    message_id=msg.id,
                    conversation_id=conv_id,
                )
                return msg.id
        except Exception as e:
            logger.error("save_assistant_message_error", error=str(e))
            return None

    def update_conversation_title(self, title: str) -> None:
        """Update the conversation title (e.g., from first user message).

        Args:
            title: The new title for the conversation.
        """
        if not self.conversation_id:
            return

        try:
            with self._get_session() as session:
                repo = ConversationRepository(session)
                # Use first 50 chars of the message as title
                truncated_title = title[:50] + "..." if len(title) > 50 else title
                repo.update(self.conversation_id, title=truncated_title)
                logger.debug(
                    "conversation_title_updated",
                    conversation_id=self.conversation_id,
                    title=truncated_title,
                )
        except Exception as e:
            logger.error("update_conversation_title_error", error=str(e))

    def resume_conversation(
        self, conversation_id: str, context: ConversationContext
    ) -> bool:
        """Resume an existing conversation by loading its messages into context.

        Args:
            conversation_id: The conversation ID to resume.
            context: The ConversationContext to populate with history.

        Returns:
            True if conversation was found and loaded, False otherwise.
        """
        try:
            with self._get_session() as session:
                conv_repo = ConversationRepository(session)
                msg_repo = MessageRepository(session)

                conv = conv_repo.get(conversation_id)
                if conv is None:
                    logger.warning(
                        "resume_conversation_not_found",
                        conversation_id=conversation_id,
                    )
                    return False

                # Load messages and populate context
                messages = msg_repo.list_by_conversation(conversation_id, limit=100)
                for msg in messages:
                    if msg.role == "user":
                        context.add_user_message(msg.content)
                    else:
                        context.add_assistant_message(msg.content)

                self.conversation_id = conversation_id
                logger.info(
                    "conversation_resumed",
                    conversation_id=conversation_id,
                    message_count=len(messages),
                )
                return True

        except Exception as e:
            logger.error("resume_conversation_error", error=str(e))
            return False

    def get_latest_conversation_id(self) -> str | None:
        """Get the ID of the most recent conversation.

        Returns:
            The conversation ID if one exists, None otherwise.
        """
        try:
            with self._get_session() as session:
                repo = ConversationRepository(session)
                latest = repo.get_latest()
                return latest.id if latest else None
        except Exception as e:
            logger.error("get_latest_conversation_error", error=str(e))
            return None


async def handle_llm_completion(
    websocket: WebSocket,
    text: str,
    context: ConversationContext,
    client_info: str,
    conversation_session: ConversationSession,
    e2e_start_time: float | None = None,
) -> None:
    """Handle LLM completion after STT with streaming response and TTS.

    Args:
        websocket: The WebSocket connection.
        text: The transcribed text from STT.
        context: The conversation context for maintaining history.
        client_info: Client identification string for logging.
        conversation_session: Session for persisting messages to DB.
        e2e_start_time: Start time for E2E latency measurement (from vad.end).
    """
    if not text.strip():
        logger.debug("llm_skip_empty_text", client=client_info)
        return

    # Add user message to context
    context.add_user_message(text)

    try:
        # Send llm.start event
        await websocket.send_json({"type": "llm.start"})
        logger.info("llm_start_sent", client=client_info)

        llm_service = get_llm_service()
        start_time = time.perf_counter()
        ttft: float | None = None
        full_response = ""

        # Sentence buffer for TTS streaming
        sentence_buffer = SentenceBuffer()
        tts_total_latency = 0.0
        is_first_tts_chunk = True  # Track first TTS chunk for E2E latency

        async for token in llm_service.stream_completion(context.get_messages()):
            if ttft is None:
                ttft = (time.perf_counter() - start_time) * 1000

            full_response += token
            await websocket.send_json({"type": "llm.delta", "text": token})

            # Buffer tokens and process complete sentences for TTS
            sentences = sentence_buffer.add(token)
            for sentence in sentences:
                try:
                    tts_latency = await handle_tts_streaming(
                        websocket,
                        sentence,
                        client_info,
                        e2e_start_time=e2e_start_time,
                        is_first_chunk=is_first_tts_chunk,
                    )
                    is_first_tts_chunk = False  # Only first chunk gets E2E timing
                    tts_total_latency += tts_latency
                except Exception as e:
                    logger.error(
                        "tts_streaming_error",
                        client=client_info,
                        sentence=sentence[:50],
                        error=str(e),
                    )
                    await websocket.send_json(
                        {
                            "type": "error",
                            "code": "TTS_ERROR",
                            "message": "音声合成に失敗しました",
                        }
                    )

        latency_ms = (time.perf_counter() - start_time) * 1000

        # Add assistant response to context
        context.add_assistant_message(full_response)

        # Send llm.end event
        await websocket.send_json(
            {
                "type": "llm.end",
                "latency_ms": round(latency_ms, 2),
                "ttft_ms": round(ttft or 0, 2),
            }
        )

        logger.info(
            "llm_completed",
            client=client_info,
            response_length=len(full_response),
            latency_ms=round(latency_ms, 2),
            ttft_ms=round(ttft or 0, 2),
        )

        # Flush remaining text in sentence buffer for TTS
        remaining = sentence_buffer.flush()
        if remaining:
            try:
                tts_latency = await handle_tts_streaming(
                    websocket,
                    remaining,
                    client_info,
                    e2e_start_time=e2e_start_time,
                    is_first_chunk=is_first_tts_chunk,
                )
                is_first_tts_chunk = False  # Mark as consumed
                tts_total_latency += tts_latency
            except Exception as e:
                logger.error(
                    "tts_flush_error",
                    client=client_info,
                    remaining=remaining[:50],
                    error=str(e),
                )

        # Send tts.end event with total TTS latency
        await websocket.send_json(
            {
                "type": "tts.end",
                "latency_ms": round(tts_total_latency, 2),
            }
        )

        logger.info(
            "tts_completed",
            client=client_info,
            total_latency_ms=round(tts_total_latency, 2),
        )

        # Save assistant message to database with latency info
        conversation_session.save_assistant_message(
            text=full_response,
            llm_latency_ms=latency_ms,
            tts_latency_ms=tts_total_latency,
        )

    except RateLimitError:
        logger.warning("llm_rate_limit", client=client_info)
        await websocket.send_json(
            {
                "type": "error",
                "code": "LLM_RATE_LIMIT",
                "message": "APIレート制限に達しました。しばらく待ってから再試行してください。",
            }
        )
    except AuthenticationError:
        logger.error("llm_auth_error", client=client_info)
        await websocket.send_json(
            {
                "type": "error",
                "code": "LLM_AUTH_ERROR",
                "message": "LLM APIの認証に失敗しました。APIキーを確認してください。",
            }
        )
    except APIError as e:
        logger.error("llm_api_error", client=client_info, error=str(e))
        await websocket.send_json(
            {
                "type": "error",
                "code": "LLM_API_ERROR",
                "message": f"LLM APIエラー: {str(e)}",
            }
        )
    except Exception as e:
        logger.error("llm_unexpected_error", client=client_info, error=str(e))
        await websocket.send_json(
            {
                "type": "error",
                "code": "LLM_ERROR",
                "message": "LLM処理中にエラーが発生しました",
            }
        )


async def handle_vad_end(
    websocket: WebSocket,
    audio_buffer: AudioBuffer,
    context: ConversationContext,
    conversation_session: ConversationSession,
    client_info: str,
) -> None:
    """Handle vad.end event by running STT and then LLM.

    Args:
        websocket: The WebSocket connection.
        audio_buffer: Buffer containing accumulated audio data.
        context: The conversation context for maintaining history.
        conversation_session: Session for persisting messages to DB.
        client_info: Client identification string for logging.
    """
    if not audio_buffer.has_audio():
        logger.debug("vad_end_no_audio", client=client_info)
        return

    # Record E2E start time for latency measurement
    e2e_start_time = time.perf_counter()

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

        # Continue to LLM processing if we got text
        if result.text.strip():
            # Save user message to database
            is_first_message = conversation_session.conversation_id is None
            conversation_session.save_user_message(result.text, int(result.latency_ms))

            # Set conversation title from first message
            if is_first_message:
                conversation_session.update_conversation_title(result.text)

            await handle_llm_completion(
                websocket,
                result.text,
                context,
                client_info,
                conversation_session,
                e2e_start_time,
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
    context: ConversationContext,
    conversation_session: ConversationSession,
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
            # Process audio with STT, then LLM
            await handle_vad_end(
                websocket, audio_buffer, context, conversation_session, client_info
            )

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
    # Each WebSocket connection has its own conversation context (in-memory)
    conversation_context = ConversationContext()
    # Each WebSocket connection has its own conversation session (DB persistence)
    conversation_session = ConversationSession()

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
                        conversation_context,
                        conversation_session,
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
