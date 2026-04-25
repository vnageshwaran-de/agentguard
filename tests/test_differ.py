"""Tests for differ.diff_traces."""

from __future__ import annotations

from agentprdiff import LLMCall, ToolCall, Trace
from agentprdiff.differ import diff_traces
from agentprdiff.graders import contains


def _trace(output: str, tools: list[str] | None = None, cost: float = 0.0, latency: float = 0.0) -> Trace:
    t = Trace(suite_name="s", case_name="c", input="x", output=output)
    for name in tools or []:
        t.record_tool_call(ToolCall(name=name))
    if cost or latency:
        t.record_llm_call(LLMCall(provider="m", model="m", cost_usd=cost, latency_ms=latency))
    return t


def test_identical_traces_no_regression():
    base = _trace("hello refund")
    cur = _trace("hello refund")
    grader = contains("refund")
    delta = diff_traces(
        baseline=base,
        current=cur,
        current_results=[grader(cur)],
        baseline_results=[grader(base)],
    )
    assert delta.has_regression is False
    assert delta.output_changed is False


def test_assertion_regression_detected():
    base = _trace("refund processed")
    cur = _trace("not today")
    grader = contains("refund")
    delta = diff_traces(
        baseline=base,
        current=cur,
        current_results=[grader(cur)],
        baseline_results=[grader(base)],
    )
    assert delta.has_regression is True
    regressions = delta.regressions
    assert len(regressions) == 1
    assert regressions[0].grader_name.startswith("contains")


def test_improvement_detected():
    base = _trace("nope")
    cur = _trace("refund issued")
    grader = contains("refund")
    delta = diff_traces(
        baseline=base,
        current=cur,
        current_results=[grader(cur)],
        baseline_results=[grader(base)],
    )
    assert delta.has_regression is False
    assert len(delta.improvements) == 1


def test_cost_and_latency_deltas():
    base = _trace("x", cost=0.001, latency=100)
    cur = _trace("x", cost=0.004, latency=300)
    delta = diff_traces(baseline=base, current=cur, current_results=[])
    assert abs(delta.cost_delta_usd - 0.003) < 1e-9
    assert abs(delta.latency_delta_ms - 200.0) < 1e-6


def test_tool_sequence_change_flagged():
    base = _trace("x", tools=["a", "b"])
    cur = _trace("x", tools=["b", "a"])
    delta = diff_traces(baseline=base, current=cur, current_results=[])
    assert delta.tool_sequence_changed is True


def test_output_diff_includes_unified_diff():
    base = _trace("hello\nworld")
    cur = _trace("hello\nmoon")
    delta = diff_traces(baseline=base, current=cur, current_results=[])
    assert delta.output_changed is True
    assert "-world" in delta.output_diff
    assert "+moon" in delta.output_diff
