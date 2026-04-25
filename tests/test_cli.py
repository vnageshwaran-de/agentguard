"""CLI smoke tests via click's CliRunner.

We invoke `agentguard record` and `agentguard check` against the bundled
quickstart suite to make sure the wiring is correct end-to-end.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from click.testing import CliRunner

from agentguard.cli import main

EXAMPLES = Path(__file__).resolve().parent.parent / "examples" / "quickstart"


def test_init_creates_directories(tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ["--root", ".agentguard", "init"])
        assert result.exit_code == 0, result.output
        assert Path(".agentguard/baselines").exists()
        assert Path(".agentguard/runs").exists()


def test_record_then_check_on_quickstart(tmp_path):
    # Copy the quickstart example into an isolated workdir so tests don't
    # leak baselines into the repo.
    work = tmp_path / "qs"
    shutil.copytree(EXAMPLES, work)

    runner = CliRunner()

    result = runner.invoke(
        main, ["--root", str(work / ".agentguard"), "record", str(work / "suite.py")]
    )
    assert result.exit_code == 0, result.output

    # Record must have created baselines.
    baselines = list((work / ".agentguard" / "baselines").rglob("*.json"))
    assert len(baselines) >= 4

    # Second run should be clean.
    result = runner.invoke(
        main, ["--root", str(work / ".agentguard"), "check", str(work / "suite.py")]
    )
    assert result.exit_code == 0, result.output
    assert "no regressions" in result.output.lower()


def test_diff_command_prints_baseline_json(tmp_path):
    work = tmp_path / "qs"
    shutil.copytree(EXAMPLES, work)

    runner = CliRunner()
    runner.invoke(
        main, ["--root", str(work / ".agentguard"), "record", str(work / "suite.py")]
    )
    result = runner.invoke(
        main,
        [
            "--root",
            str(work / ".agentguard"),
            "diff",
            "customer_support",
            "refund_happy_path",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "customer_support" in result.output
    assert "refund_happy_path" in result.output
