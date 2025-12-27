"""API layer for Voice Assistant"""

from voice_assistant.api.websocket import router as ws_router

__all__ = ["ws_router"]
