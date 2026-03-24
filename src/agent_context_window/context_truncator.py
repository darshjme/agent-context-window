"""ContextTruncator: Truncates text/messages to fit token limits."""

from __future__ import annotations

from typing import Literal

from .token_counter import TokenCounter

TruncateStrategy = Literal["end", "middle", "start"]


class ContextTruncator:
    """Truncates text or message lists to fit within a token budget.

    Parameters
    ----------
    model:
        Model name forwarded to :class:`TokenCounter`.
    """

    def __init__(self, model: str = "gpt-4") -> None:
        self._counter = TokenCounter(model)

    # ------------------------------------------------------------------
    # Text truncation
    # ------------------------------------------------------------------

    def truncate(
        self,
        text: str,
        max_tokens: int,
        strategy: TruncateStrategy = "end",
    ) -> str:
        """Truncate *text* so it fits within *max_tokens*.

        Parameters
        ----------
        text:
            Input string.
        max_tokens:
            Maximum allowed tokens.
        strategy:
            * ``"end"``    — keep the beginning, drop the tail.
            * ``"start"``  — keep the end, drop the head.
            * ``"middle"`` — keep both ends, drop the middle section.
        """
        if strategy not in ("end", "middle", "start"):
            raise ValueError(f"Unknown truncation strategy: {strategy!r}")
        if max_tokens <= 0:
            return ""
        if self._counter.fits(text, max_tokens):
            return text

        # Binary-search to find character boundary that satisfies the limit.
        # chars/token ratio gives a tight starting estimate.
        ratio = self._counter._ratio
        target_chars = int(max_tokens * ratio)

        if strategy == "end":
            # Keep head
            candidate = text[:target_chars]
            # Trim 1 char at a time if still over (edge case: multibyte / short ratio)
            while self._counter.count(candidate) > max_tokens and candidate:
                candidate = candidate[:-1]
            return candidate

        elif strategy == "start":
            # Keep tail
            candidate = text[-target_chars:] if target_chars < len(text) else text
            while self._counter.count(candidate) > max_tokens and candidate:
                candidate = candidate[1:]
            return candidate

        elif strategy == "middle":
            # Keep both ends, drop the middle
            half = target_chars // 2
            head = text[:half]
            tail = text[-half:] if half < len(text) else ""
            candidate = head + tail
            # Trim edges if still over
            while self._counter.count(candidate) > max_tokens and (head or tail):
                if head:
                    head = head[:-1]
                if tail:
                    tail = tail[1:]
                candidate = head + tail
            return candidate

        else:
            raise ValueError(f"Unknown truncation strategy: {strategy!r}")

    # ------------------------------------------------------------------
    # Placeholder helper
    # ------------------------------------------------------------------

    def summarize_placeholder(self, token_count: int) -> str:
        """Return a human-readable omission placeholder."""
        return f"[{token_count} tokens omitted]"

    # ------------------------------------------------------------------
    # Message list truncation
    # ------------------------------------------------------------------

    def fit_messages(
        self,
        messages: list[dict],
        max_tokens: int,
    ) -> list[dict]:
        """Remove or truncate messages until the list fits within *max_tokens*.

        Strategy:
        1. If the full list already fits, return it unchanged.
        2. Drop messages from the *front* (oldest first) until within budget.
           System messages (role == "system") are protected and never dropped.
        3. If a single large non-system message still exceeds the budget,
           truncate its content with the ``"end"`` strategy.
        """
        if self._counter.count_messages(messages) <= max_tokens:
            return list(messages)

        # Separate system messages (always kept) from the rest
        system_msgs = [m for m in messages if m.get("role", "").lower() == "system"]
        other_msgs = [m for m in messages if m.get("role", "").lower() != "system"]

        # Drop oldest non-system messages first
        while other_msgs:
            candidate = system_msgs + other_msgs
            if self._counter.count_messages(candidate) <= max_tokens:
                break
            other_msgs.pop(0)

        result = system_msgs + other_msgs

        # Final safety: truncate last message content if still over
        if self._counter.count_messages(result) > max_tokens and result:
            last = dict(result[-1])
            system_budget = self._counter.count_messages(result[:-1])
            remaining = max_tokens - system_budget
            if remaining > 0:
                last["content"] = self.truncate(
                    last.get("content", ""), remaining, strategy="end"
                )
            else:
                last["content"] = ""
            result = result[:-1] + [last]

        return result
