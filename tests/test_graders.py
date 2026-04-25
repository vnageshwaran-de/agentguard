"""Tests for every grader."""

from __future__ import annotations

from agentguard.graders import (
    contains,
    contains_any,
    cost_lt_usd,
    fake_judge,
    latency_lt_ms,
    no_tool_called,
    output_length_lt,
    regex_match,
    semantic,
    tool_called,
    tool_sequence,
)


class TestDeterministicGraders:
    def test_contains_case_insensitive(self, make_trace):
        t = make_trace(output="Your REFUND has been processed.")
        assert contains("refund")(t).passed is True
        assert contains("missing")(t).passed is False

    def test_contains_case_sensitive(self, make_trace):
        t = make_trace(output="REFUND approved")
        assert contains("refund", case_sensitive=True)(t).passed is False
        assert contains("REFUND", case_sensitive=True)(t).passed is True

    def test_contains_any(self, make_trace):
        t = make_trace(output="I cannot process this")
        assert contains_any(["refund", "cannot"])(t).passed is True
        assert contains_any(["xyz", "qqq"])(t).passed is False

    def test_regex_match(self, make_trace):
        t = make_trace(output="Order #1234 refunded")
        assert regex_match(r"Order #\d+")(t).passed is True
        assert regex_match(r"nope")(t).passed is False

    def test_tool_called(self, make_trace):
        t = make_trace(tools=["lookup_order", "refund", "lookup_order"])
        assert tool_called("lookup_order")(t).passed is True
        assert tool_called("lookup_order", min_times=2)(t).passed is True
        assert tool_called("lookup_order", min_times=3)(t).passed is False
        assert tool_called("send_email")(t).passed is False

    def test_no_tool_called(self, make_trace):
        t = make_trace(tools=["lookup_order"])
        assert no_tool_called("send_email")(t).passed is True
        assert no_tool_called("lookup_order")(t).passed is False

    def test_tool_sequence_subsequence(self, make_trace):
        t = make_trace(tools=["a", "b", "c", "d"])
        assert tool_sequence(["a", "c"])(t).passed is True
        assert tool_sequence(["c", "a"])(t).passed is False

    def test_tool_sequence_strict(self, make_trace):
        t = make_trace(tools=["a", "b"])
        assert tool_sequence(["a", "b"], strict=True)(t).passed is True
        assert tool_sequence(["a", "b", "c"], strict=True)(t).passed is False

    def test_output_length_lt(self, make_trace):
        t = make_trace(output="hi")
        assert output_length_lt(10)(t).passed is True
        assert output_length_lt(2)(t).passed is False

    def test_latency_lt_ms(self, make_trace):
        t = make_trace(latency=500)
        assert latency_lt_ms(1000)(t).passed is True
        assert latency_lt_ms(100)(t).passed is False

    def test_cost_lt_usd(self, make_trace):
        t = make_trace(cost=0.001)
        assert cost_lt_usd(0.01)(t).passed is True
        assert cost_lt_usd(0.0001)(t).passed is False


class TestSemanticGrader:
    def test_fake_judge_matches_keywords(self, make_trace):
        t = make_trace(output="We have refunded your order in full.")
        passed, _ = fake_judge("agent confirmed a refund was processed", t)
        assert passed is True

    def test_fake_judge_rejects_empty_output(self, make_trace):
        t = make_trace(output="")
        passed, _ = fake_judge("agent confirmed a refund", t)
        assert passed is False

    def test_semantic_uses_supplied_judge(self, make_trace):
        calls = {"n": 0}

        def my_judge(rubric: str, trace):
            calls["n"] += 1
            return True, f"looked at {rubric[:10]}"

        t = make_trace(output="ok")
        result = semantic("some rubric", judge=my_judge)(t)
        assert result.passed is True
        assert calls["n"] == 1

    def test_semantic_survives_judge_exception(self, make_trace):
        def bad_judge(rubric, trace):
            raise RuntimeError("boom")

        t = make_trace(output="ok")
        result = semantic("x", judge=bad_judge)(t)
        assert result.passed is False
        assert "boom" in result.reason
