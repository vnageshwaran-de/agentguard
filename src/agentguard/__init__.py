"""agentguard — snapshot testing for LLM agents.

The one-happy-path public API:

    from agentguard import suite, case
    from agentguard.graders import contains, tool_called, latency_lt_ms, semantic

    def my_agent(query: str) -> str:
        ...

    billing_suite = suite(
        name="billing",
        agent=my_agent,
        cases=[
            case(
                name="refund_happy_path",
                input="I want a refund for order #1234",
                expect=[
                    contains("refund"),
                    tool_called("lookup_order"),
                    semantic("agent acknowledges the refund and provides next steps"),
                    latency_lt_ms(10_000),
                ],
            ),
        ],
    )

Run from the shell::

    agentguard init
    agentguard record path/to/my_suite.py     # save baselines
    agentguard check  path/to/my_suite.py     # diff against baselines; exit 1 on regression
"""

from __future__ import annotations

from .core import (
    AgentFn,
    Case,
    Grader,
    GradeResult,
    LLMCall,
    Suite,
    ToolCall,
    Trace,
    case,
    run_agent,
    suite,
)
from .differ import AssertionChange, TraceDelta, diff_traces
from .runner import CaseReport, Runner, RunReport
from .store import BaselineStore

__version__ = "0.1.0"

__all__ = [
    # core
    "Suite",
    "Case",
    "Trace",
    "LLMCall",
    "ToolCall",
    "Grader",
    "GradeResult",
    "AgentFn",
    "suite",
    "case",
    "run_agent",
    # diffing
    "TraceDelta",
    "AssertionChange",
    "diff_traces",
    # runner
    "Runner",
    "RunReport",
    "CaseReport",
    # storage
    "BaselineStore",
    # version
    "__version__",
]
