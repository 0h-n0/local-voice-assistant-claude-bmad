"""Base classes for LLM service layer."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field


@dataclass
class ConversationContext:
    """Manages conversation history for LLM context.

    Maintains a rolling window of messages to provide context
    to the LLM while staying within token limits.
    """

    max_messages: int = 10
    messages: list[dict[str, str]] = field(default_factory=list)
    system_prompt: str = "あなたは親切な日本語アシスタントです。簡潔で自然な日本語で応答してください。"

    def add_user_message(self, text: str) -> None:
        """Add a user message to the context."""
        self.messages.append({"role": "user", "content": text})
        self._trim()

    def add_assistant_message(self, text: str) -> None:
        """Add an assistant message to the context."""
        self.messages.append({"role": "assistant", "content": text})
        self._trim()

    def get_messages(self) -> list[dict[str, str]]:
        """Get all messages including system prompt for LLM API call."""
        return [
            {"role": "system", "content": self.system_prompt},
            *self.messages,
        ]

    def clear(self) -> None:
        """Clear all messages from context."""
        self.messages = []

    def _trim(self) -> None:
        """Trim old messages to stay within max_messages limit."""
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages :]


class BaseLLM(ABC):
    """Abstract base class for LLM services.

    Defines the interface for streaming LLM completions.
    """

    @abstractmethod
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
        pass
        # Make this an async generator
        yield ""  # pragma: no cover
