"""Sentence buffer for text splitting in TTS processing."""


class SentenceBuffer:
    """Buffer for splitting text into sentences.

    Accumulates text chunks and yields complete sentences
    when sentence-ending punctuation is detected.
    """

    def __init__(self) -> None:
        self.buffer = ""
        self.sentence_endings = "。！？\n"

    def add(self, text: str) -> list[str]:
        """Add text to buffer and return completed sentences.

        Args:
            text: Text chunk to add.

        Returns:
            List of complete sentences (may be empty if no sentences completed).
        """
        self.buffer += text
        sentences: list[str] = []

        while True:
            # Find the first sentence ending
            earliest_idx = -1
            for ending in self.sentence_endings:
                idx = self.buffer.find(ending)
                if idx != -1:
                    if earliest_idx == -1 or idx < earliest_idx:
                        earliest_idx = idx

            if earliest_idx == -1:
                break

            # Extract the sentence (including the ending character)
            sentence = self.buffer[: earliest_idx + 1].strip()
            if sentence:
                sentences.append(sentence)
            self.buffer = self.buffer[earliest_idx + 1 :]

        return sentences

    def flush(self) -> str | None:
        """Flush remaining buffered text.

        Returns:
            Remaining text if any, None if buffer is empty.
        """
        if self.buffer.strip():
            result = self.buffer.strip()
            self.buffer = ""
            return result
        return None
