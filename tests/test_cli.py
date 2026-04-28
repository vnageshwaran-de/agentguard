"""CLI smoke tests via click's CliRunner.

We invoke `agentprdiff record` and `agentprdiff check` against the bundled
quickstart suite to make sure the wiring is correct end-to-end.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from click.testing import CliRunner

from agentprdiff.cli import main

EXAMPLES = Path(__file__).resolve().parent.parent / "examples" / "quickstart"


def test_init_creates_directories(tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, ["--root", ".agentprdiff", "init"])
        assert result.exit_code == 0, result.output
        assert Path(".agentprdiff/baselines").exists()
        assert Path(".agentprdiff/runs").exists()


def test_record_then_check_on_quickstart(tmp_path):
    # Copy the quickstart example into an isolated workdir so tests don't
    # leak baselines into the repo.
    work = tmp_path / "qs"
    shutil.copytree(EXAMPLES, work)

    runner = CliRunner()

    result = runner.invoke(
        main, ["--root", str(work / ".agentprdiff"), "record", str(work / "suite.py")]
    )
    assert result.exit_code == 0, result.output

    # Record must have created baselines.
    baselines = list((work / ".agentprdiff" / "baselines").rglob("*.json"))
    assert len(baselines) >= 4

    # Second run should be clean.
    result = runner.invoke(
        main, ["--root", str(work / ".agentprdiff"), "check", str(work / "suite.py")]
    )
    assert result.exit_code == 0, result.output
    assert "no regressions" in result.output.lower()


def test_diff_command_prints_baseline_json(tmp_path):
    work = tmp_path / "qs"
    shutil.copytree(EXAMPLES, work)

    runner = CliRunner()
    runner.invoke(
        main, ["--root", str(work / ".agentprdiff"), "record", str(work / "suite.py")]
    )
    result = runner.invoke(
        main,
        [
            "--root",
            str(work / ".agentprdiff"),
            "diff",
            "customer_support",
            "refund_happy_path",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "customer_support" in result.output
    assert "refund_happy_path" in result.output


# ---------------------------------------------------------------------------
# --case / --skip / --list
# ---------------------------------------------------------------------------


def _record_baselines(tmp_path):
    """Helper: copy quickstart and record baselines, return the workdir."""
    work = tmp_path / "qs"
    shutil.copytree(EXAMPLES, work)
    runner = CliRunner()
    result = runner.invoke(
        main, ["--root", str(work / ".agentprdiff"), "record", str(work / "suite.py")]
    )
    assert result.exit_code == 0, result.output
    return work


def test_list_flag_prints_cases_without_running(tmp_path):
    work = tmp_path / "qs"
    shutil.copytree(EXAMPLES, work)
    runner = CliRunner()

    result = runner.invoke(
        main,
        [
            "--root",
            str(work / ".agentprdiff"),
            "check",
            str(work / "suite.py"),
            "--list",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "customer_support" in result.output
    assert "refund_happy_path" in result.output
    assert "policy_question_no_tools" in result.output
    # We listed cases but didn't run them, so the rich-rendered run table
    # and the trailing summary line should both be absent.
    assert "no regressions" not in result.output.lower()
    assert "Result" not in result.output  # rich table header
    assert "PASS" not in result.output


def test_case_filter_runs_only_matching_cases(tmp_path):
    work = _record_baselines(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        main,
        [
            "--root",
            str(work / ".agentprdiff"),
            "check",
            str(work / "suite.py"),
            "--case",
            "refund",
        ],
    )
    assert result.exit_code == 0, result.output
    # "refund" substring matches refund_happy_path AND non_refundable_order.
    assert "running 2 of 4 cases in customer_support" in result.output
    assert "refund_happy_path" in result.output
    assert "non_refundable_order" in result.output
    # The unrelated cases should NOT appear in the rendered table.
    assert "policy_question_no_tools" not in result.output
    assert "missing_order_number" not in result.output


def test_case_filter_supports_glob(tmp_path):
    work = _record_baselines(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        main,
        [
            "--root",
            str(work / ".agentprdiff"),
            "check",
            str(work / "suite.py"),
            "--case",
            "*order*",
        ],
    )
    assert result.exit_code == 0, result.output
    # non_refundable_order and missing_order_number both contain "order".
    assert "running 2 of 4 cases" in result.output
    assert "non_refundable_order" in result.output
    assert "missing_order_number" in result.output


def test_case_filter_accepts_comma_separated(tmp_path):
    work = _record_baselines(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        main,
        [
            "--root",
            str(work / ".agentprdiff"),
            "check",
            str(work / "suite.py"),
            "--case",
            "refund,policy",
        ],
    )
    assert result.exit_code == 0, result.output
    # refund matches 2 cases, policy matches 1 → 3 of 4.
    assert "running 3 of 4 cases" in result.output
    assert "policy_question_no_tools" in result.output


def test_case_filter_accepts_repeated_flags(tmp_path):
    work = _record_baselines(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        main,
        [
            "--root",
            str(work / ".agentprdiff"),
            "check",
            str(work / "suite.py"),
            "--case",
            "refund",
            "--case",
            "policy",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "running 3 of 4 cases" in result.output


def test_skip_flag_drops_matching_cases(tmp_path):
    work = _record_baselines(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        main,
        [
            "--root",
            str(work / ".agentprdiff"),
            "check",
            str(work / "suite.py"),
            "--skip",
            "policy",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "running 3 of 4 cases" in result.output
    assert "policy_question_no_tools" not in result.output


def test_case_negation_equivalent_to_skip(tmp_path):
    work = _record_baselines(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        main,
        [
            "--root",
            str(work / ".agentprdiff"),
            "check",
            str(work / "suite.py"),
            "--case",
            "~policy",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "running 3 of 4 cases" in result.output
    assert "policy_question_no_tools" not in result.output


def test_zero_match_filter_exits_2(tmp_path):
    work = _record_baselines(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        main,
        [
            "--root",
            str(work / ".agentprdiff"),
            "check",
            str(work / "suite.py"),
            "--case",
            "this_will_never_match_xyz",
        ],
    )
    # Distinct from regression (1) and success (0).
    assert result.exit_code == 2, result.output
    # Surface the available case names so a typo is fixable from the error.
    assert "no cases matched" in result.output.lower()
    assert "refund_happy_path" in result.output


def test_record_respects_case_filter(tmp_path):
    """--case should narrow `record` too — only matching cases get baselines."""
    work = tmp_path / "qs"
    shutil.copytree(EXAMPLES, work)
    runner = CliRunner()

    result = runner.invoke(
        main,
        [
            "--root",
            str(work / ".agentprdiff"),
            "record",
            str(work / "suite.py"),
            "--case",
            "refund_happy_path",
        ],
    )
    assert result.exit_code == 0, result.output
    baselines = list((work / ".agentprdiff" / "baselines").rglob("*.json"))
    assert len(baselines) == 1
    assert "refund_happy_path" in baselines[0].name
