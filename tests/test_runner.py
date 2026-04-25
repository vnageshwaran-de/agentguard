"""End-to-end runner tests.

These exercise the full record → check workflow with a small in-process
agent. They are the most important tests in the suite: if these pass,
agentprdiff's core loop works.
"""

from __future__ import annotations

from agentprdiff import LLMCall, ToolCall, Trace, case, suite
from agentprdiff.graders import contains, cost_lt_usd, no_tool_called, tool_called
from agentprdiff.runner import Runner
from agentprdiff.store import BaselineStore


def toy_agent(query: str) -> tuple[str, Trace]:
    """Returns different output / tool calls for different inputs."""
    t = Trace(suite_name="", case_name="", input=query)
    t.record_llm_call(LLMCall(provider="m", model="m", cost_usd=0.001, latency_ms=10))
    if "refund" in query:
        t.record_tool_call(ToolCall(name="lookup_order"))
        return "refund processed", t
    return "please share your order number", t


def _build_suite():
    return suite(
        name="toy",
        agent=toy_agent,
        cases=[
            case(
                name="refund",
                input="can I get a refund",
                expect=[contains("refund"), tool_called("lookup_order"), cost_lt_usd(0.01)],
            ),
            case(
                name="no_tools",
                input="hello",
                expect=[contains("order"), no_tool_called("lookup_order")],
            ),
        ],
    )


def test_record_then_check_is_green(tmp_path):
    store = BaselineStore(root=tmp_path / ".agentprdiff")
    runner = Runner(store)

    s = _build_suite()
    rec = runner.record(s)
    assert rec.cases_passed == 2

    chk = runner.check(s)
    assert chk.cases_passed == 2
    assert chk.has_regression is False
    # All baselines should exist after record.
    assert store.load_baseline("toy", "refund") is not None
    assert store.load_baseline("toy", "no_tools") is not None


def test_check_detects_regression_when_agent_behavior_changes(tmp_path):
    store = BaselineStore(root=tmp_path / ".agentprdiff")
    runner = Runner(store)

    s = _build_suite()
    runner.record(s)

    # Swap to a broken agent and rebuild the suite.
    def broken_agent(query: str) -> tuple[str, Trace]:
        t = Trace(suite_name="", case_name="", input=query)
        # Returns the wrong response for 'refund', no tool call.
        return "hello there", t

    s_broken = suite(name="toy", agent=broken_agent, cases=s.cases)
    chk = runner.check(s_broken)
    assert chk.has_regression is True
    # The 'refund' case should regress on the contains + tool_called assertions.
    refund_case = next(c for c in chk.case_reports if c.case_name == "refund")
    assert refund_case.has_regression is True
    assert refund_case.passed is False


def test_first_run_with_failing_assertion_counts_as_regression(tmp_path):
    store = BaselineStore(root=tmp_path / ".agentprdiff")
    runner = Runner(store)
    s = suite(
        name="toy",
        agent=toy_agent,
        cases=[case(name="bad", input="hi", expect=[contains("does-not-exist")])],
    )
    # No baseline recorded. A failing first run is still a regression.
    chk = runner.check(s)
    assert chk.has_regression is True


def test_agent_exception_is_captured(tmp_path):
    store = BaselineStore(root=tmp_path / ".agentprdiff")
    runner = Runner(store)

    def raising_agent(q):
        raise ValueError("oops")

    s = suite(name="s", agent=raising_agent, cases=[case(name="c", input="x", expect=[])])
    chk = runner.check(s)
    assert chk.case_reports[0].trace.error is not None
    assert "ValueError" in chk.case_reports[0].trace.error
    assert chk.has_regression is True
