# agent-context-window

> **Context window management for LLM agents** — token counting, sliding window, content prioritization, and truncation strategies. Zero dependencies. Python 3.10+.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## The Problem

LLM context windows have hard limits (GPT-4: 128K, Claude: 200K tokens). Long agent conversations hit these limits and crash — or silently truncate your prompt in unpredictable ways.

```
ConversationTooLongError: This model's maximum context length is 128000 tokens.
Your messages resulted in 131072 tokens. Reduce the length of the messages.
```

**agent-context-window** solves this before it reaches the API.

---

## Installation

```bash
pip install agent-context-window
```

Or from source:
```bash
git clone https://github.com/darshjme-codes/agent-context-window
cd agent-context-window
pip install -e .
```

---

## Quick Start: Context Overflow Prevention

```python
from agent_context_window import ContextWindow, TokenCounter, ContentPrioritizer, ContextTruncator

# --- Setup ---
window = ContextWindow(max_tokens=128_000, reserve_tokens=4_096)
counter = TokenCounter(model="gpt-4")
prioritizer = ContentPrioritizer()
truncator = ContextTruncator(model="gpt-4")

# --- Build up a long conversation ---
window.add_message("system", "You are a helpful coding assistant.", priority=10)

for i in range(200):
    window.add_message("user", f"Step {i}: Please help me debug this function: " + "x" * 500)
    window.add_message("assistant", f"Step {i} response: Here's the fix..." + "y" * 300)

# --- Check usage ---
print(f"Messages stored:   {len(window)}")
print(f"Token usage:       {window.token_usage:,} / {window.max_tokens:,}")
print(f"Available tokens:  {window.available_tokens:,}")
print(f"Window is full:    {window.is_full}")

# --- Get messages safe to send to API ---
messages = window.get_messages()
print(f"Messages in window: {len(messages)}")

# --- Prioritize: keep the most important messages ---
reranked = prioritizer.rerank(messages)
print(f"Top message role: {reranked[0]['role']}")

# --- Truncate a single big document to fit in 1000 tokens ---
big_doc = "This is a very long document. " * 1000
truncated = truncator.truncate(big_doc, max_tokens=1_000, strategy="end")
print(f"Truncated tokens: {counter.count(truncated)}")

# --- Fit an entire message list into a tight budget ---
fitted = truncator.fit_messages(messages[:10], max_tokens=500)
print(f"Fitted messages: {len(fitted)}")

# --- Check if text fits before sending ---
user_input = "Summarize the above conversation."
if counter.fits(user_input, window.available_tokens):
    window.add_message("user", user_input)
    print("Message added successfully")
else:
    window.prune(strategy="oldest")
    window.add_message("user", user_input)
    print("Pruned oldest and added message")
```

---

## Components

### `TokenCounter`

Approximates token counts without any API calls using a chars/token ratio.

```python
from agent_context_window import TokenCounter

tc = TokenCounter(model="gpt-4")           # or "claude-3-opus", "gemini-1.5-pro"

tc.count("Hello world")                    # → 3
tc.count_messages([                        # → ~25 tokens
    {"role": "system", "content": "Be helpful."},
    {"role": "user",   "content": "Hi!"},
])
tc.fits("short text", max_tokens=100)     # → True
tc.available(used_tokens=5000)            # → 123000
```

**Supported models** (others fall back to 4.0 chars/token):
`gpt-4`, `gpt-4o`, `gpt-3.5-turbo`, `claude-3-*`, `gemini-*`

---

### `ContextWindow`

Sliding window that auto-prunes when the token budget is exceeded.

```python
from agent_context_window import ContextWindow

cw = ContextWindow(max_tokens=128_000, reserve_tokens=4_096)

cw.add_message("system",    "You are helpful.",  priority=10)
cw.add_message("user",      "Tell me a joke.",   priority=0)
cw.add_message("assistant", "Why did the...",    priority=0)

cw.token_usage       # current token count
cw.available_tokens  # remaining budget
cw.is_full           # True when no space left

cw.get_messages()    # → list[dict] ready for the LLM API

# Manual pruning
cw.prune(strategy="oldest")           # drop chronologically first message
cw.prune(strategy="lowest_priority")  # drop lowest-priority message
```

---

### `ContentPrioritizer`

Scores messages by importance and re-ranks them.

```python
from agent_context_window import ContentPrioritizer

cp = ContentPrioritizer()

cp.score({"role": "system",    "content": "..."})          # → 1.0 (always max)
cp.score({"role": "user",      "content": "normal text"})  # → ~0.3
cp.score({"role": "assistant", "content": "critical error occurred"})  # → ~0.5

# Re-rank: system messages first, then by keyword score + recency
ranked = cp.rerank(messages)
```

**Scoring rules:**
| Condition | Score |
|-----------|-------|
| `role == "system"` | `1.0` (fixed) |
| Base score | `0.3` |
| Each keyword match (`error`, `critical`, `important`, `urgent`, …) | `+0.1` (max `+0.4`) |
| Recency bonus (during `rerank`) | `+0.0` → `+0.3` |

---

### `ContextTruncator`

Truncates text or message lists to fit token budgets.

```python
from agent_context_window import ContextTruncator

ct = ContextTruncator(model="gpt-4")

# Text truncation strategies
ct.truncate(long_text, max_tokens=500, strategy="end")    # keep head
ct.truncate(long_text, max_tokens=500, strategy="start")  # keep tail
ct.truncate(long_text, max_tokens=500, strategy="middle") # keep both ends

# Placeholder for summarized content
ct.summarize_placeholder(1500)  # → "[1500 tokens omitted]"

# Fit an entire message list (drops oldest, preserves system messages)
ct.fit_messages(messages, max_tokens=2000)
```

---

## Why No Dependencies?

Zero runtime dependencies means:
- ✅ No version conflicts with your LLM SDK
- ✅ Works in any Python 3.10+ environment
- ✅ Lightweight — suitable for serverless / edge
- ✅ No tiktoken, no transformers, no torch required

The 4-chars-per-token approximation is accurate to ±15% for natural language, which is sufficient for safe context management (the reserve buffer handles edge cases).

---

## Development

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

---

## License

MIT © Darshankumar Joshi
