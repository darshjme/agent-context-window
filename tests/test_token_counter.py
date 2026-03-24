"""Tests for TokenCounter."""

import pytest
from agent_context_window import TokenCounter


class TestTokenCounterInit:
    def test_default_model(self):
        tc = TokenCounter()
        assert tc.model == "gpt-4"

    def test_custom_model(self):
        tc = TokenCounter("claude-3-opus")
        assert tc.model == "claude-3-opus"

    def test_unknown_model_falls_back_to_4(self):
        tc = TokenCounter("some-future-model")
        assert tc._ratio == 4.0


class TestTokenCounterCount:
    def test_empty_string(self):
        assert TokenCounter().count("") == 0

    def test_single_char(self):
        # 1 char → ceil(1/4) = 1
        assert TokenCounter().count("a") == 1

    def test_four_chars(self):
        assert TokenCounter().count("abcd") == 1

    def test_five_chars(self):
        assert TokenCounter().count("abcde") == 2

    def test_long_text(self):
        text = "a" * 400
        # 400 chars / 4 = 100
        assert TokenCounter().count(text) == 100

    def test_whitespace_only(self):
        assert TokenCounter().count("    ") == 1


class TestTokenCounterCountMessages:
    def test_empty_list(self):
        tc = TokenCounter()
        assert tc.count_messages([]) == 3  # reply primer only

    def test_single_message(self):
        tc = TokenCounter()
        msgs = [{"role": "user", "content": "Hello"}]
        result = tc.count_messages(msgs)
        # 3 (primer) + 4 (overhead) + count("user") + count("Hello")
        assert result > 3

    def test_multiple_messages(self):
        tc = TokenCounter()
        msgs = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
        ]
        result = tc.count_messages(msgs)
        assert result > tc.count_messages(msgs[:1])


class TestTokenCounterFits:
    def test_fits_true(self):
        tc = TokenCounter()
        assert tc.fits("short", 100) is True

    def test_fits_false(self):
        tc = TokenCounter()
        long_text = "x" * 10_000  # ~2500 tokens
        assert tc.fits(long_text, 100) is False

    def test_fits_exact_boundary(self):
        tc = TokenCounter()
        text = "a" * 400  # exactly 100 tokens
        assert tc.fits(text, 100) is True
        assert tc.fits(text, 99) is False


class TestTokenCounterAvailable:
    def test_no_usage(self):
        assert TokenCounter().available(0) == 128_000

    def test_partial_usage(self):
        assert TokenCounter().available(1000) == 127_000

    def test_over_limit(self):
        assert TokenCounter().available(200_000) == 0

    def test_custom_limit(self):
        assert TokenCounter().available(50_000, model_limit=200_000) == 150_000
