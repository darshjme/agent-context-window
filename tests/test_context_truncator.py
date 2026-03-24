"""Tests for ContextTruncator."""

import pytest
from agent_context_window import ContextTruncator, TokenCounter


class TestContextTruncatorTruncate:
    def setup_method(self):
        self.ct = ContextTruncator()

    def test_short_text_unchanged(self):
        text = "Hello world"
        assert self.ct.truncate(text, 100) == text

    def test_end_strategy_keeps_head(self):
        text = "ABCDEFGHIJ" * 100  # ~250 tokens
        result = self.ct.truncate(text, 50, strategy="end")
        tc = TokenCounter()
        assert tc.count(result) <= 50
        assert result.startswith("ABCD")

    def test_start_strategy_keeps_tail(self):
        text = "ABCDEFGHIJ" * 100
        result = self.ct.truncate(text, 50, strategy="start")
        tc = TokenCounter()
        assert tc.count(result) <= 50
        assert result.endswith("ABCDEFGHIJ")

    def test_middle_strategy_removes_center(self):
        text = "START" + ("x" * 1000) + "END"
        result = self.ct.truncate(text, 10, strategy="middle")
        tc = TokenCounter()
        assert tc.count(result) <= 10

    def test_zero_max_returns_empty(self):
        assert self.ct.truncate("some text", 0) == ""

    def test_unknown_strategy_raises(self):
        with pytest.raises(ValueError):
            self.ct.truncate("text", 10, strategy="random")  # type: ignore

    def test_empty_text_unchanged(self):
        assert self.ct.truncate("", 100) == ""


class TestContextTruncatorPlaceholder:
    def test_placeholder_format(self):
        ct = ContextTruncator()
        assert ct.summarize_placeholder(500) == "[500 tokens omitted]"
        assert ct.summarize_placeholder(0) == "[0 tokens omitted]"
        assert ct.summarize_placeholder(1) == "[1 tokens omitted]"


class TestContextTruncatorFitMessages:
    def setup_method(self):
        self.ct = ContextTruncator()
        self.tc = TokenCounter()

    def test_already_fits(self):
        messages = [{"role": "user", "content": "Hi"}]
        result = self.ct.fit_messages(messages, 10_000)
        assert result == messages

    def test_removes_oldest_first(self):
        messages = [
            {"role": "user", "content": "First very old message"},
            {"role": "user", "content": "Second older message"},
            {"role": "user", "content": "Third recent message"},
        ]
        # Force a tight budget (just enough for ~2 messages)
        budget = self.tc.count_messages(messages[-2:]) + 5
        result = self.ct.fit_messages(messages, budget)
        contents = [m["content"] for m in result]
        assert "Third recent message" in contents

    def test_system_messages_never_dropped(self):
        system = {"role": "system", "content": "You are helpful."}
        messages = [system] + [
            {"role": "user", "content": f"Message {i} with some filler text"}
            for i in range(10)
        ]
        # Budget only allows for a couple messages but system must stay
        result = self.ct.fit_messages(messages, 50)
        roles = [m["role"] for m in result]
        assert "system" in roles

    def test_empty_messages(self):
        assert self.ct.fit_messages([], 1000) == []

    def test_result_fits_within_budget(self):
        messages = [
            {"role": "user", "content": "x" * 500}
            for _ in range(10)
        ]
        budget = 200
        result = self.ct.fit_messages(messages, budget)
        assert self.tc.count_messages(result) <= budget
