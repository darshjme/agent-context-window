"""ContextWindow: Sliding window conversation manager."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Literal

from .token_counter import TokenCounter


@dataclass
class _Message:
    role: str
    content: str
    priority: int
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


PruneStrategy = Literal["oldest", "lowest_priority"]


class ContextWindow:
    """Manages a sliding window of conversation messages within a token budget.

    Parameters
    ----------
    max_tokens:
        Hard limit on total tokens in the window (e.g. 128 000 for GPT-4).
    reserve_tokens:
        Tokens reserved for the model's reply (subtracted from usable budget).
    model:
        Model name forwarded to TokenCounter for ratio selection.
    """

    def __init__(
        self,
        max_tokens: int = 128_000,
        reserve_tokens: int = 4_096,
        model: str = "gpt-4",
    ) -> None:
        if max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        if reserve_tokens < 0:
            raise ValueError("reserve_tokens must be non-negative")
        if reserve_tokens >= max_tokens:
            raise ValueError("reserve_tokens must be less than max_tokens")

        self.max_tokens = max_tokens
        self.reserve_tokens = reserve_tokens
        self._counter = TokenCounter(model)
        self._messages: list[_Message] = []

    # ------------------------------------------------------------------
    # Budget helpers
    # ------------------------------------------------------------------

    @property
    def _budget(self) -> int:
        """Usable token budget (max minus reserve)."""
        return self.max_tokens - self.reserve_tokens

    @property
    def token_usage(self) -> int:
        """Current approximate token usage of all stored messages."""
        return self._counter.count_messages([m.to_dict() for m in self._messages])

    @property
    def available_tokens(self) -> int:
        """Tokens available before the budget is exhausted."""
        return max(0, self._budget - self.token_usage)

    @property
    def is_full(self) -> bool:
        """True when adding any more content would exceed the budget."""
        return self.available_tokens == 0

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add_message(self, role: str, content: str, priority: int = 0) -> None:
        """Append a message to the window.

        If the new message would push usage over budget, :meth:`prune` is
        called automatically with the ``"oldest"`` strategy until space exists
        (or the window cannot be pruned further).
        """
        msg = _Message(role=role, content=content, priority=priority)
        self._messages.append(msg)

        # Auto-prune if over budget
        while self.token_usage > self._budget and len(self._messages) > 1:
            self.prune(strategy="oldest")

    def prune(self, strategy: PruneStrategy = "oldest") -> None:
        """Remove one message according to *strategy*.

        ``"oldest"``
            Removes the chronologically first message (index 0).
        ``"lowest_priority"``
            Removes the message with the lowest priority value; ties broken
            by age (oldest first).
        """
        if not self._messages:
            return

        if strategy == "oldest":
            self._messages.pop(0)
        elif strategy == "lowest_priority":
            # Find index of lowest-priority (then oldest) message
            idx = min(
                range(len(self._messages)),
                key=lambda i: (self._messages[i].priority, self._messages[i].timestamp),
            )
            self._messages.pop(idx)
        else:
            raise ValueError(f"Unknown prune strategy: {strategy!r}")

    def clear(self) -> None:
        """Remove all messages."""
        self._messages.clear()

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get_messages(self) -> list[dict]:
        """Return messages that fit within the token budget as plain dicts."""
        return [m.to_dict() for m in self._messages]

    def __len__(self) -> int:
        return len(self._messages)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ContextWindow(messages={len(self._messages)}, "
            f"usage={self.token_usage}/{self._budget})"
        )
