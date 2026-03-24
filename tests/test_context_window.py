"""Tests for ContextWindow."""

import pytest
from agent_context_window import ContextWindow


class TestContextWindowInit:
    def test_defaults(self):
        cw = ContextWindow()
        assert cw.max_tokens == 128_000
        assert cw.reserve_tokens == 4_096

    def test_custom(self):
        cw = ContextWindow(max_tokens=8000, reserve_tokens=512)
        assert cw.max_tokens == 8000
        assert cw.reserve_tokens == 512

    def test_invalid_max_tokens(self):
        with pytest.raises(ValueError):
            ContextWindow(max_tokens=0)

    def test_reserve_exceeds_max(self):
        with pytest.raises(ValueError):
            ContextWindow(max_tokens=100, reserve_tokens=100)


class TestContextWindowBasic:
    def test_empty_window(self):
        cw = ContextWindow()
        assert cw.get_messages() == []
        assert len(cw) == 0

    def test_add_and_get(self):
        cw = ContextWindow()
        cw.add_message("user", "Hello")
        msgs = cw.get_messages()
        assert len(msgs) == 1
        assert msgs[0]["role"] == "user"
        assert msgs[0]["content"] == "Hello"

    def test_token_usage_increases(self):
        cw = ContextWindow()
        before = cw.token_usage
        cw.add_message("user", "Hello, world!")
        assert cw.token_usage > before

    def test_available_tokens_decreases(self):
        cw = ContextWindow()
        before = cw.available_tokens
        cw.add_message("assistant", "Some response text here.")
        assert cw.available_tokens < before

    def test_is_full_false_initially(self):
        cw = ContextWindow()
        assert cw.is_full is False

    def test_clear(self):
        cw = ContextWindow()
        cw.add_message("user", "Hi")
        cw.clear()
        assert len(cw) == 0
        assert cw.get_messages() == []


class TestContextWindowPrune:
    def test_prune_oldest(self):
        cw = ContextWindow(max_tokens=10000, reserve_tokens=100)
        cw.add_message("user", "First")
        cw.add_message("user", "Second")
        cw.add_message("user", "Third")
        cw.prune(strategy="oldest")
        msgs = cw.get_messages()
        assert msgs[0]["content"] == "Second"

    def test_prune_lowest_priority(self):
        cw = ContextWindow(max_tokens=10000, reserve_tokens=100)
        cw.add_message("user", "Low priority", priority=0)
        cw.add_message("user", "High priority", priority=10)
        cw.prune(strategy="lowest_priority")
        msgs = cw.get_messages()
        assert len(msgs) == 1
        assert msgs[0]["content"] == "High priority"

    def test_prune_empty_window(self):
        cw = ContextWindow()
        cw.prune()  # should not raise

    def test_prune_unknown_strategy(self):
        cw = ContextWindow(max_tokens=10000, reserve_tokens=100)
        cw.add_message("user", "test")
        with pytest.raises(ValueError):
            cw.prune(strategy="random")  # type: ignore

    def test_auto_prune_on_overflow(self):
        # Tiny budget to force auto-prune
        cw = ContextWindow(max_tokens=200, reserve_tokens=10)
        for i in range(20):
            cw.add_message("user", f"Message number {i} with some text to fill tokens")
        # Should not exceed budget
        assert cw.token_usage <= cw._budget
