"""Deterministic graders — cheap, free, reproducible.

These never call an LLM. Prefer them whenever the assertion can be expressed
mechanically; reserve the semantic grader for things you genuinely can't
encode as a rule.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from ..core import Grader, GradeResult, Trace


def _output_str(trace: Trace) -> str:
    """Best-effort stringification of the agent's final output."""
    out = trace.output
    if out is None:
        return ""
    if isinstance(out, str):
        return out
    try:
        return str(out)
    except Exception:  # noqa: BLE001
        return ""


def contains(substring: str, *, case_sensitive: bool = False) -> Grader:
    """Pass iff the agent's final output contains `substring`."""

    def _grader(trace: Trace) -> GradeResult:
        haystack = _output_str(trace)
        passed = (
            substring in haystack if case_sensitive else substring.lower() in haystack.lower()
        )
        return GradeResult(
            passed=passed,
            grader_name=f"contains({substring!r})",
            reason=(
                f"output {'contains' if passed else 'does not contain'} {substring!r}"
            ),
        )

    return _grader


def contains_any(substrings: Sequence[str], *, case_sensitive: bool = False) -> Grader:
    """Pass iff the output contains at least one of the listed substrings."""

    def _grader(trace: Trace) -> GradeResult:
        haystack = _output_str(trace) if case_sensitive else _output_str(trace).lower()
        needles = list(substrings) if case_sensitive else [s.lower() for s in substrings]
        matched = [n for n in needles if n in haystack]
        passed = bool(matched)
        return GradeResult(
            passed=passed,
            grader_name=f"contains_any({list(substrings)!r})",
            reason=(
                f"matched {matched!r}"
                if passed
                else f"none of {list(substrings)!r} found in output"
            ),
        )

    return _grader


def regex_match(pattern: str, *, flags: int = 0) -> Grader:
    """Pass iff `pattern` matches the agent's final output."""
    compiled = re.compile(pattern, flags=flags)

    def _grader(trace: Trace) -> GradeResult:
        haystack = _output_str(trace)
        m = compiled.search(haystack)
        passed = m is not None
        return GradeResult(
            passed=passed,
            grader_name=f"regex_match({pattern!r})",
            reason=(
                f"matched {m.group(0)!r}" if m else f"no match for {pattern!r}"
            ),
        )

    return _grader


def tool_called(name: str, *, min_times: int = 1) -> Grader:
    """Pass iff the tool `name` was called at least `min_times` times."""

    def _grader(trace: Trace) -> GradeResult:
        count = sum(1 for c in trace.tool_calls if c.name == name)
        passed = count >= min_times
        return GradeResult(
            passed=passed,
            grader_name=f"tool_called({name!r}, min_times={min_times})",
            reason=f"tool {name!r} called {count} time(s), required >= {min_times}",
        )

    return _grader


def no_tool_called(name: str) -> Grader:
    """Pass iff the tool `name` was NOT called."""

    def _grader(trace: Trace) -> GradeResult:
        count = sum(1 for c in trace.tool_calls if c.name == name)
        passed = count == 0
        return GradeResult(
            passed=passed,
            grader_name=f"no_tool_called({name!r})",
            reason=f"tool {name!r} called {count} time(s); expected 0",
        )

    return _grader


def tool_sequence(sequence: Sequence[str], *, strict: bool = False) -> Grader:
    """Pass iff the tool-call sequence matches `sequence`.

    If `strict=False` (default), `sequence` must appear as a subsequence of
    the actual tool calls (other tools may be interleaved). If `strict=True`,
    the tool calls must equal `sequence` exactly.
    """

    def _grader(trace: Trace) -> GradeResult:
        actual = [c.name for c in trace.tool_calls]
        if strict:
            passed = actual == list(sequence)
        else:
            # subsequence check
            i = 0
            for call in actual:
                if i < len(sequence) and call == sequence[i]:
                    i += 1
            passed = i == len(sequence)
        return GradeResult(
            passed=passed,
            grader_name=f"tool_sequence({list(sequence)!r}, strict={strict})",
            reason=f"actual tool sequence: {actual}",
        )

    return _grader


def output_length_lt(max_chars: int) -> Grader:
    """Pass iff the output has fewer than `max_chars` characters."""

    def _grader(trace: Trace) -> GradeResult:
        n = len(_output_str(trace))
        passed = n < max_chars
        return GradeResult(
            passed=passed,
            grader_name=f"output_length_lt({max_chars})",
            reason=f"output length {n} chars, limit {max_chars}",
        )

    return _grader


def latency_lt_ms(max_ms: float) -> Grader:
    """Pass iff the trace's total latency is below `max_ms` milliseconds."""

    def _grader(trace: Trace) -> GradeResult:
        passed = trace.total_latency_ms < max_ms
        return GradeResult(
            passed=passed,
            grader_name=f"latency_lt_ms({max_ms})",
            reason=f"latency {trace.total_latency_ms:.1f} ms, limit {max_ms:.1f} ms",
        )

    return _grader


def cost_lt_usd(max_usd: float) -> Grader:
    """Pass iff the trace's total cost is below `max_usd` dollars."""

    def _grader(trace: Trace) -> GradeResult:
        passed = trace.total_cost_usd < max_usd
        return GradeResult(
            passed=passed,
            grader_name=f"cost_lt_usd({max_usd})",
            reason=f"cost ${trace.total_cost_usd:.4f}, limit ${max_usd:.4f}",
        )

    return _grader
