"""Reporters — render RunReports for humans and for CI.

`TerminalReporter` uses rich for pretty output. `JsonReporter` writes a
stable JSON envelope you can archive as a CI artifact.
"""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .runner import RunReport


class TerminalReporter:
    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def render(self, report: RunReport) -> None:
        header = Text()
        header.append(f"agentguard {report.mode} ", style="bold cyan")
        header.append("— suite ", style="dim")
        header.append(f"{report.suite_name}", style="bold")
        header.append(
            f"  ({report.cases_passed}/{report.cases_total} passed, "
            f"{report.cases_regressed} regressed)",
            style="dim",
        )
        self.console.print(header)

        table = Table(show_header=True, header_style="bold", show_lines=False, expand=True)
        table.add_column("Case", style="bold")
        table.add_column("Result")
        table.add_column("Cost Δ", justify="right")
        table.add_column("Latency Δ", justify="right")
        table.add_column("Notes")

        for cr in report.case_reports:
            if cr.has_regression:
                result = Text("REGRESSION", style="bold red")
            elif cr.passed:
                result = Text("PASS", style="bold green")
            else:
                result = Text("FAIL", style="bold red")

            cost_cell = ""
            latency_cell = ""
            notes = []
            if cr.delta is not None:
                if cr.delta.cost_delta_usd:
                    cost_cell = _format_delta(cr.delta.cost_delta_usd, "${:+.4f}")
                if cr.delta.latency_delta_ms:
                    latency_cell = _format_delta(cr.delta.latency_delta_ms, "{:+.0f} ms")
                if cr.delta.tool_sequence_changed:
                    notes.append(
                        "tools: "
                        f"{cr.delta.baseline_tool_sequence} → "
                        f"{cr.delta.current_tool_sequence}"
                    )
                if cr.delta.output_changed and not cr.has_regression:
                    notes.append("output changed")
                for ac in cr.delta.regressions:
                    notes.append(f"[red]{ac.grader_name}[/red] {ac.current_reason}")
            if cr.trace.error:
                notes.append(f"[red]error:[/red] {cr.trace.error}")
            for r in cr.grader_results:
                if not r.passed and cr.delta is None:
                    notes.append(f"[red]{r.grader_name}[/red] {r.reason}")

            table.add_row(cr.case_name, result, cost_cell, latency_cell, "\n".join(notes) or "—")

        self.console.print(table)

        # Per-regression expanded section.
        for cr in report.case_reports:
            if cr.has_regression and cr.delta is not None and cr.delta.output_diff:
                self.console.print(
                    Panel(
                        cr.delta.output_diff,
                        title=f"{cr.case_name}: output diff",
                        border_style="red",
                    )
                )

        if report.mode == "check":
            if report.has_regression:
                self.console.print(
                    Text(
                        f"\n✗ {report.cases_regressed} regression(s) detected.",
                        style="bold red",
                    )
                )
            else:
                self.console.print(Text("\n✓ no regressions.", style="bold green"))


class JsonReporter:
    """Write a stable JSON envelope suitable for CI artifact archiving."""

    def render(self, report: RunReport, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "suite": report.suite_name,
            "mode": report.mode,
            "summary": {
                "cases_total": report.cases_total,
                "cases_passed": report.cases_passed,
                "cases_regressed": report.cases_regressed,
                "has_regression": report.has_regression,
            },
            "cases": [cr.model_dump(mode="json") for cr in report.case_reports],
        }
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return path


def _format_delta(value: float, fmt: str) -> str:
    if value == 0:
        return ""
    text = fmt.format(value)
    color = "green" if value < 0 else "red"
    return f"[{color}]{text}[/{color}]"
