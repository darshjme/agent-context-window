"""TokenCounter: Approximate token counting without API calls."""

from __future__ import annotations

# chars-per-token ratios for common models (empirically tuned)
MODEL_RATIOS: dict[str, float] = {
    "gpt-4": 4.0,
    "gpt-4o": 4.0,
    "gpt-3.5-turbo": 4.0,
    "claude-3-opus": 3.8,
    "claude-3-sonnet": 3.8,
    "claude-3-haiku": 3.8,
    "claude-sonnet-4": 3.8,
    "gemini-1.5-pro": 4.0,
    "gemini-2.0-flash": 4.0,
    # overhead per message in OpenAI-style message format
}

# Per-message overhead (role label, formatting tokens)
MESSAGE_OVERHEAD = 4


class TokenCounter:
    """Approximates token counts for LLM inputs without calling any API.

    Uses a characters-per-token ratio specific to the chosen model family.
    The default ratio of 4.0 chars/token matches GPT-4 / tiktoken's cl100k_base
    empirically (±15 % on natural language).
    """

    def __init__(self, model: str = "gpt-4") -> None:
        self.model = model
        # Look up ratio; fall back to 4.0 for unknown models
        self._ratio: float = MODEL_RATIOS.get(model.lower(), 4.0)

    # ------------------------------------------------------------------
    # Core helpers
    # ------------------------------------------------------------------

    def count(self, text: str) -> int:
        """Approximate token count for *text*.

        Formula: ceil(len(text) / ratio).  Returns 0 for empty strings.
        """
        if not text:
            return 0
        return max(1, -(-len(text) // int(self._ratio)))  # ceiling division

    def count_messages(self, messages: list[dict]) -> int:
        """Approximate total tokens for a list of role/content dicts.

        Each message incurs MESSAGE_OVERHEAD tokens on top of its content.
        An extra 3 tokens are added for the reply-primer the API inserts.
        """
        total = 3  # reply primer
        for msg in messages:
            total += MESSAGE_OVERHEAD
            role = msg.get("role", "")
            content = msg.get("content", "")
            total += self.count(role)
            if isinstance(content, str):
                total += self.count(content)
            elif isinstance(content, list):
                # Multi-modal / tool-call style content blocks
                for block in content:
                    if isinstance(block, dict):
                        total += self.count(block.get("text", ""))
                    elif isinstance(block, str):
                        total += self.count(block)
        return total

    def fits(self, text: str, max_tokens: int) -> bool:
        """Return True if *text* fits within *max_tokens*."""
        return self.count(text) <= max_tokens

    def available(self, used_tokens: int, model_limit: int = 128_000) -> int:
        """Tokens remaining given *used_tokens* already consumed."""
        return max(0, model_limit - used_tokens)
