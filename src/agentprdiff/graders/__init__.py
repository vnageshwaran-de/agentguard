"""Graders — assertions over a `Trace`.

Every grader returns a `GradeResult`. Deterministic graders (cheap, free,
no LLM calls) live in `deterministic.py`. The `semantic` grader uses an
LLM-as-judge backend — it lives in `semantic.py` and is pluggable.

The names exposed from this module form `agentprdiff`'s public assertion API.
Keep the surface area small and stable.
"""

from __future__ import annotations

from .deterministic import (
    contains,
    contains_any,
    cost_lt_usd,
    latency_lt_ms,
    no_tool_called,
    output_length_lt,
    regex_match,
    tool_called,
    tool_sequence,
)
from .semantic import fake_judge, semantic

__all__ = [
    "contains",
    "contains_any",
    "regex_match",
    "tool_called",
    "tool_sequence",
    "no_tool_called",
    "output_length_lt",
    "latency_lt_ms",
    "cost_lt_usd",
    "semantic",
    "fake_judge",
]
