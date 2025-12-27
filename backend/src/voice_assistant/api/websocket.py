"""WebSocket endpoint for real-time voice chat"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from voice_assistant.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.websocket("/api/v1/ws/chat")
async def websocket_chat(websocket: WebSocket) -> None:
    """WebSocket endpoint for voice chat.

    Handles real-time bidirectional communication between frontend and backend.
    Future stories will add event handling for VAD, STT, LLM, and TTS.

    Args:
        websocket: The WebSocket connection.
    """
    await websocket.accept()
    client_info = str(websocket.client) if websocket.client else "unknown"
    logger.info("websocket_connected", client=client_info)

    try:
        while True:
            # Keep connection alive and wait for messages
            # Event processing will be added in Story 2.2+
            data = await websocket.receive_text()
            # Echo back for now (basic ping-pong for connection verification)
            await websocket.send_text(data)
    except WebSocketDisconnect:
        logger.info("websocket_disconnected", client=client_info)
