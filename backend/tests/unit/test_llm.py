"""Unit tests for LLM service layer."""

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from voice_assistant.llm.base import BaseLLM, ConversationContext
from voice_assistant.llm.openai_compat import OpenAICompatLLM


class TestConversationContext:
    """Tests for ConversationContext class."""

    def test_init_empty(self) -> None:
        """Test empty context initialization."""
        ctx = ConversationContext()
        assert ctx.messages == []
        assert ctx.max_messages == 10

    def test_init_custom_max(self) -> None:
        """Test context with custom max_messages."""
        ctx = ConversationContext(max_messages=5)
        assert ctx.max_messages == 5

    def test_add_user_message(self) -> None:
        """Test adding user message."""
        ctx = ConversationContext()
        ctx.add_user_message("Hello")
        assert len(ctx.messages) == 1
        assert ctx.messages[0] == {"role": "user", "content": "Hello"}

    def test_add_assistant_message(self) -> None:
        """Test adding assistant message."""
        ctx = ConversationContext()
        ctx.add_assistant_message("Hi there!")
        assert len(ctx.messages) == 1
        assert ctx.messages[0] == {"role": "assistant", "content": "Hi there!"}

    def test_get_messages_includes_system(self) -> None:
        """Test get_messages includes system prompt."""
        ctx = ConversationContext()
        ctx.add_user_message("Hello")
        messages = ctx.get_messages()
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1] == {"role": "user", "content": "Hello"}

    def test_trim_old_messages(self) -> None:
        """Test trimming old messages when max exceeded."""
        ctx = ConversationContext(max_messages=3)
        for i in range(5):
            ctx.add_user_message(f"Message {i}")
        assert len(ctx.messages) == 3
        # Should keep last 3 messages
        assert ctx.messages[0]["content"] == "Message 2"
        assert ctx.messages[2]["content"] == "Message 4"

    def test_clear(self) -> None:
        """Test clearing context."""
        ctx = ConversationContext()
        ctx.add_user_message("Hello")
        ctx.add_assistant_message("Hi")
        ctx.clear()
        assert ctx.messages == []


class TestOpenAICompatLLM:
    """Tests for OpenAICompatLLM class."""

    def test_init_defaults(self) -> None:
        """Test default initialization."""
        llm = OpenAICompatLLM()
        assert llm.model == "gpt-4o-mini"
        assert llm.client is not None

    def test_init_custom(self) -> None:
        """Test custom initialization."""
        llm = OpenAICompatLLM(
            api_key="test-key",
            base_url="http://localhost:11434/v1",
            model="llama3.2",
        )
        assert llm.model == "llama3.2"

    @pytest.mark.asyncio
    async def test_stream_completion_yields_tokens(self) -> None:
        """Test streaming completion yields tokens."""
        llm = OpenAICompatLLM(api_key="test")

        # Mock the async stream
        mock_chunk1 = MagicMock()
        mock_chunk1.choices = [MagicMock(delta=MagicMock(content="Hello"))]

        mock_chunk2 = MagicMock()
        mock_chunk2.choices = [MagicMock(delta=MagicMock(content=" world"))]

        mock_chunk3 = MagicMock()
        mock_chunk3.choices = [MagicMock(delta=MagicMock(content=None))]

        async def mock_stream() -> AsyncIterator[MagicMock]:
            for chunk in [mock_chunk1, mock_chunk2, mock_chunk3]:
                yield chunk

        with patch.object(
            llm.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_stream(),
        ):
            messages = [{"role": "user", "content": "Hi"}]
            tokens = []
            async for token in llm.stream_completion(messages):
                tokens.append(token)

            assert tokens == ["Hello", " world"]

    @pytest.mark.asyncio
    async def test_stream_completion_handles_empty_content(self) -> None:
        """Test streaming handles chunks with empty content."""
        llm = OpenAICompatLLM(api_key="test")

        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock(delta=MagicMock(content=""))]

        async def mock_stream() -> AsyncIterator[MagicMock]:
            yield mock_chunk

        with patch.object(
            llm.client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_stream(),
        ):
            messages = [{"role": "user", "content": "Hi"}]
            tokens = []
            async for token in llm.stream_completion(messages):
                tokens.append(token)

            assert tokens == []


class TestBaseLLM:
    """Tests for BaseLLM abstract class."""

    def test_is_abstract(self) -> None:
        """Test BaseLLM cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseLLM()  # type: ignore
