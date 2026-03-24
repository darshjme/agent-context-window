"""ContentPrioritizer: Ranks messages by importance."""

from __future__ import annotations

import re

# Keywords that elevate a message's importance score
_HIGH_IMPORTANCE_KEYWORDS: frozenset[str] = frozenset(
    {
        "error",
        "critical",
        "important",
        "urgent",
        "warning",
        "fatal",
        "exception",
        "failure",
        "must",
        "required",
        "mandatory",
        "alert",
        "issue",
    }
)

_KEYWORD_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in _HIGH_IMPORTANCE_KEYWORDS) + r")\b",
    re.IGNORECASE,
)


class ContentPrioritizer:
    """Scores and re-ranks messages by their estimated importance.

    Scoring rules (additive, clamped to [0.0, 1.0]):
    - ``system`` role → base score 1.0 (always maximum)
    - Other roles start at 0.3
    - Each high-importance keyword match adds 0.1 (up to +0.4)
    - Recency bonus applied during :meth:`rerank` (not :meth:`score`)
    """

    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score(self, message: dict) -> float:
        """Score a single message's importance in [0.0, 1.0].

        Does **not** factor in recency (that requires the full list).
        Use :meth:`rerank` for recency-aware ordering.
        """
        role: str = message.get("role", "").lower()
        content: str = message.get("content", "") or ""

        if role == "system":
            return 1.0

        base = 0.3
        # Keyword bonus
        matches = len(_KEYWORD_PATTERN.findall(content))
        keyword_bonus = min(0.4, matches * 0.1)
        raw = base + keyword_bonus
        return round(min(1.0, raw), 4)

    def rerank(self, messages: list[dict]) -> list[dict]:
        """Return a *new* list sorted by importance (highest first).

        Recency bonus: messages later in the original list receive a
        proportional bonus up to +0.3, so recent messages rank higher
        when keyword scores are equal.
        """
        n = len(messages)
        if n == 0:
            return []

        scored: list[tuple[float, int, dict]] = []
        for idx, msg in enumerate(messages):
            base_score = self.score(msg)
            # Recency: 0.0 (oldest) → 0.3 (newest)
            recency_bonus = (idx / max(n - 1, 1)) * 0.3 if n > 1 else 0.0
            # System messages keep max score regardless of recency
            if msg.get("role", "").lower() == "system":
                total = 1.0
            else:
                total = round(min(1.0, base_score + recency_bonus), 4)
            scored.append((total, idx, msg))

        # Sort descending by score; ties broken by original index (later = higher)
        scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
        return [item[2] for item in scored]
