"""OpenAI-compatible LLM client implementation."""

import os
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from voice_assistant.core.logging import get_logger
from voice_assistant.llm.base import BaseLLM

logger = get_logger(__name__)


class OpenAICompatLLM(BaseLLM):
    """OpenAI API-compatible LLM client.

    Supports OpenAI, Ollama, Groq, and other OpenAI-compatible APIs.

    Example usage:
        # For Ollama
        llm = OpenAICompatLLM(
            base_url="http://localhost:11434/v1",
            model="llama3.2"
        )

        # For OpenAI
        llm = OpenAICompatLLM(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini"
        )

        # For Groq
        llm = OpenAICompatLLM(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1",
            model="llama-3.1-70b-versatile"
        )
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "gpt-4o-mini",
    ) -> None:
        """Initialize OpenAI-compatible LLM client.

        Args:
            api_key: API key for authentication. Defaults to OPENAI_API_KEY env var.
                     For Ollama, any non-empty string works.
            base_url: Base URL for API. Defaults to OPENAI_BASE_URL env var or OpenAI.
                     For Ollama: "http://localhost:11434/v1"
            model: Model name to use.
        """
        self.model = model

        # Resolve API key from environment if not provided
        resolved_api_key = api_key or os.getenv("OPENAI_API_KEY", "ollama")

        # Resolve base URL from environment if not provided
        resolved_base_url = base_url or os.getenv("OPENAI_BASE_URL")

        self.client = AsyncOpenAI(
            api_key=resolved_api_key,
            base_url=resolved_base_url,
        )

        logger.info(
            "llm_client_initialized",
            model=model,
            base_url=resolved_base_url or "default",
        )

    async def stream_completion(
        self,
        messages: list[dict[str, str]],
    ) -> AsyncIterator[str]:
        """Stream completion tokens from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.

        Yields:
            str: Individual tokens from the LLM response.
        """
        logger.info(
            "llm_stream_start",
            model=self.model,
            message_count=len(messages),
        )

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,  # type: ignore[arg-type]
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
