"""Tests for ContentPrioritizer."""

import pytest
from agent_context_window import ContentPrioritizer


class TestContentPrioritizerScore:
    def setup_method(self):
        self.cp = ContentPrioritizer()

    def test_system_message_is_max(self):
        msg = {"role": "system", "content": "You are a helpful assistant."}
        assert self.cp.score(msg) == 1.0

    def test_user_message_base_score(self):
        msg = {"role": "user", "content": "What time is it?"}
        score = self.cp.score(msg)
        assert 0.0 < score < 1.0

    def test_keyword_error_increases_score(self):
        plain = {"role": "user", "content": "What is the weather?"}
        with_error = {"role": "user", "content": "There was an error in the process."}
        assert self.cp.score(with_error) > self.cp.score(plain)

    def test_keyword_critical_increases_score(self):
        msg = {"role": "assistant", "content": "This is a critical failure!"}
        assert self.cp.score(msg) > 0.3

    def test_multiple_keywords_higher_score(self):
        one_kw = {"role": "user", "content": "error occurred"}
        two_kw = {"role": "user", "content": "critical error occurred important"}
        assert self.cp.score(two_kw) > self.cp.score(one_kw)

    def test_score_capped_at_1(self):
        msg = {"role": "user", "content": "error critical important urgent warning fatal"}
        assert self.cp.score(msg) <= 1.0

    def test_score_range(self):
        for role in ("user", "assistant", "tool"):
            msg = {"role": role, "content": "some normal content here"}
            s = self.cp.score(msg)
            assert 0.0 <= s <= 1.0, f"score {s} out of range for role={role}"


class TestContentPrioritizerRerank:
    def setup_method(self):
        self.cp = ContentPrioritizer()

    def test_empty_list(self):
        assert self.cp.rerank([]) == []

    def test_system_message_first(self):
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "assistant", "content": "Hi there!"},
        ]
        reranked = self.cp.rerank(messages)
        assert reranked[0]["role"] == "system"

    def test_recent_messages_rank_higher(self):
        messages = [
            {"role": "user", "content": "Old boring message"},
            {"role": "user", "content": "Old boring message 2"},
            {"role": "user", "content": "Recent boring message"},
        ]
        reranked = self.cp.rerank(messages)
        # Most recent should rank higher than oldest (no keywords to differentiate)
        assert reranked[0]["content"] == "Recent boring message"

    def test_high_priority_keyword_outranks_older(self):
        messages = [
            {"role": "user", "content": "critical error failure urgent warning fatal"},
            {"role": "user", "content": "Something trivial happened today"},
            {"role": "user", "content": "Nothing notable here at all"},
        ]
        reranked = self.cp.rerank(messages)
        assert "critical" in reranked[0]["content"]

    def test_rerank_preserves_all_messages(self):
        messages = [
            {"role": "user", "content": f"Message {i}"}
            for i in range(5)
        ]
        reranked = self.cp.rerank(messages)
        assert len(reranked) == 5
