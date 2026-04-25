"""Command-line interface for agentprdiff.

Four subcommands:

* `agentprdiff init`    — scaffold a .agentprdiff/ directory
* `agentprdiff record`  — record baselines for every suite in a file
* `agentprdiff check`   — compare against baselines; exit 1 on regression
* `agentprdiff diff`    — show the diff for the most recent run of a case
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from .loader import load_suites
from .reporters import JsonReporter, TerminalReporter
from .runner import Runner
from .store import BaselineStore


@click.group(help="Snapshot testing for LLM agents.")
@click.version_option(package_name="agentprdiff", prog_name="agentprdiff")
@click.option(
    "--root",
    default=".agentprdiff",
    show_default=True,
    help="Directory where baselines and runs are stored.",
)
@click.pass_context
def main(ctx: click.Context, root: str) -> None:
    ctx.ensure_object(dict)
    ctx.obj["store"] = BaselineStore(root=root)


@main.command("init")
@click.pass_context
def cmd_init(ctx: click.Context) -> None:
    """Create the .agentprdiff/ directory and a starter .gitignore."""
    store: BaselineStore = ctx.obj["store"]
    store.ensure_initialized()
    click.echo(f"initialized {store.root}/")
    click.echo(f"  baselines: {store.baselines_dir}/   (commit this)")
    click.echo(f"  runs:      {store.runs_dir}/        (gitignored)")


@main.command("record")
@click.argument("suite_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--json-out", type=click.Path(path_type=Path), help="Write JSON report to this path.")
@click.pass_context
def cmd_record(ctx: click.Context, suite_file: Path, json_out: Path | None) -> None:
    """Run every suite in SUITE_FILE and save each trace as the baseline."""
    store: BaselineStore = ctx.obj["store"]
    runner = Runner(store)
    terminal = TerminalReporter()

    suites = load_suites(suite_file)
    any_error = False
    for s in suites:
        report = runner.record(s)
        terminal.render(report)
        if json_out:
            JsonReporter().render(report, json_out)
        # record mode doesn't fail on failures, but a literal exception during
        # execution still warrants a nonzero exit.
        if any(cr.trace.error for cr in report.case_reports):
            any_error = True

    sys.exit(1 if any_error else 0)


@main.command("check")
@click.argument("suite_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--json-out", type=click.Path(path_type=Path), help="Write JSON report to this path.")
@click.option(
    "--fail-on/--no-fail-on",
    "fail_on_regression",
    default=True,
    show_default=True,
    help="Exit non-zero when regressions are detected.",
)
@click.pass_context
def cmd_check(
    ctx: click.Context,
    suite_file: Path,
    json_out: Path | None,
    fail_on_regression: bool,
) -> None:
    """Run every suite in SUITE_FILE and diff against saved baselines."""
    store: BaselineStore = ctx.obj["store"]
    runner = Runner(store)
    terminal = TerminalReporter()

    any_regression = False
    suites = load_suites(suite_file)
    for s in suites:
        report = runner.check(s)
        terminal.render(report)
        if json_out:
            JsonReporter().render(report, json_out)
        any_regression = any_regression or report.has_regression

    sys.exit(1 if (any_regression and fail_on_regression) else 0)


@main.command("diff")
@click.argument("suite_name")
@click.argument("case_name")
@click.pass_context
def cmd_diff(ctx: click.Context, suite_name: str, case_name: str) -> None:
    """Show the saved baseline trace for SUITE_NAME / CASE_NAME as pretty JSON."""
    store: BaselineStore = ctx.obj["store"]
    trace = store.load_baseline(suite_name, case_name)
    if trace is None:
        click.echo(f"no baseline found for {suite_name}/{case_name}", err=True)
        sys.exit(2)
    click.echo(json.dumps(trace.model_dump(mode="json"), indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
