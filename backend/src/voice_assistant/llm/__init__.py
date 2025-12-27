"""LLM service layer for voice assistant."""

from voice_assistant.llm.base import BaseLLM, ConversationContext
from voice_assistant.llm.openai_compat import OpenAICompatLLM

__all__ = ["BaseLLM", "ConversationContext", "OpenAICompatLLM"]
