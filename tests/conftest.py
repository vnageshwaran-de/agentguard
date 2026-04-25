"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from agentguard import LLMCall, ToolCall, Trace


@pytest.fixture
def sample_trace() -> Trace:
    t = Trace(suite_name="s", case_name="c", input="hello", output="hello refund world")
    t.record_llm_call(
        LLMCall(provider="mock", model="m", output_text="hi", cost_usd=0.001, latency_ms=100)
    )
    t.record_tool_call(ToolCall(name="lookup_order", arguments={"id": "1"}, latency_ms=5))
    return t


@pytest.fixture
def make_trace():
    def _make(output: str = "", tools: list[str] | None = None, cost: float = 0.0, latency: float = 0.0) -> Trace:
        t = Trace(suite_name="s", case_name="c", input="x", output=output)
        for name in tools or []:
            t.record_tool_call(ToolCall(name=name))
        t.total_cost_usd = cost
        t.total_latency_ms = latency
        return t

    return _make
