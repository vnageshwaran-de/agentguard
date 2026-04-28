"""Tests for `agentprdiff scaffold`."""

from __future__ import annotations

import ast

import pytest
from click.testing import CliRunner

from agentprdiff.cli import main
from agentprdiff.scaffold import VALID_RECIPES, scaffold

# ---------------------------------------------------------------------------
# Library-level
# ---------------------------------------------------------------------------


def test_scaffold_creates_all_canonical_files(tmp_path):
    result = scaffold("demo", recipe="sync-openai", root=tmp_path)
    expected = {
        tmp_path / "suites" / "__init__.py",
        tmp_path / "suites" / "_eval_agent.py",
        tmp_path / "suites" / "_stubs.py",
        tmp_path / "suites" / "demo.py",
        tmp_path / "suites" / "demo_cases.md",
        tmp_path / "suites" / "README.md",
        tmp_path / ".github" / "workflows" / "agentprdiff.yml",
    }
    assert set(result.written) == expected
    assert result.skipped == []
    for p in expected:
        assert p.exists(), p


def test_scaffold_emits_case_dossier_with_run_commands(tmp_path):
    """The dossier exists, names the suite, and shows --case usage."""
    scaffold("ai_content_summary", recipe="sync-openai", root=tmp_path)
    dossier = (tmp_path / "suites" / "ai_content_summary_cases.md").read_text()

    # Title and self-link to the suite file.
    assert "ai_content_summary" in dossier
    assert "[`ai_content_summary.py`](./ai_content_summary.py)" in dossier
    # How-to-run section includes single-case iteration.
    assert "--case happy_path" in dossier
    assert "--list" in dossier
    # Per-case skeleton uses the four-section structure.
    assert "**What it tests.**" in dossier
    assert "**Input.**" in dossier
    assert "**Assertions.**" in dossier
    assert "**Code impacted.**" in dossier
    assert "**Application impact.**" in dossier
    # The example case from the suite is referenced.
    assert "### `happy_path`" in dossier


@pytest.mark.parametrize("recipe", VALID_RECIPES)
def test_scaffold_emits_valid_python_for_every_recipe(tmp_path, recipe):
    """Every generated .py file must at least parse — TODO markers and
    `noqa: F821` references can stay because the user fills them in."""
    result = scaffold("demo", recipe=recipe, root=tmp_path)
    py_files = [p for p in result.written if p.suffix == ".py"]
    assert py_files, "scaffold produced no .py files"
    for p in py_files:
        ast.parse(p.read_text(encoding="utf-8"), filename=str(p))


def test_scaffold_workflow_has_least_privilege_permissions(tmp_path):
    pytest.importorskip("yaml")
    import yaml  # type: ignore[import-not-found]

    scaffold("demo", recipe="sync-openai", root=tmp_path)
    wf = yaml.safe_load(
        (tmp_path / ".github" / "workflows" / "agentprdiff.yml").read_text()
    )
    assert wf["permissions"] == {"contents": "read"}


def test_scaffold_workflow_references_suite_path(tmp_path):
    scaffold("ai_content_summary", recipe="sync-openai", root=tmp_path)
    wf = (tmp_path / ".github" / "workflows" / "agentprdiff.yml").read_text()
    assert "suites/ai_content_summary.py" in wf


def test_scaffold_does_not_overwrite_existing_files(tmp_path):
    # First run creates everything.
    scaffold("demo", recipe="sync-openai", root=tmp_path)
    target = tmp_path / "suites" / "demo.py"
    target.write_text("# I was here first\n", encoding="utf-8")

    # Second run must not clobber.
    result = scaffold("demo", recipe="sync-openai", root=tmp_path)
    assert target in result.skipped
    assert target.read_text() == "# I was here first\n"
    assert result.written == []  # everything else also already existed


def test_scaffold_partial_overwrite_only_skips_existing(tmp_path):
    # Pre-create only one file; the rest should still be written.
    (tmp_path / "suites").mkdir()
    existing = tmp_path / "suites" / "_stubs.py"
    existing.write_text("# pre-existing\n", encoding="utf-8")

    result = scaffold("demo", recipe="sync-openai", root=tmp_path)
    assert existing in result.skipped
    assert existing.read_text() == "# pre-existing\n"
    # Six other canonical files written (we pre-created one of seven).
    assert len(result.written) == 6


@pytest.mark.parametrize(
    "bad_name",
    ["", "1starts_with_digit", "Has-Dashes", "HasUpper", "has spaces", "has.dot"],
)
def test_scaffold_rejects_invalid_names(tmp_path, bad_name):
    with pytest.raises(ValueError, match="invalid name"):
        scaffold(bad_name, recipe="sync-openai", root=tmp_path)


def test_scaffold_rejects_unknown_recipe(tmp_path):
    with pytest.raises(ValueError, match="unknown recipe"):
        scaffold("demo", recipe="not-a-real-recipe", root=tmp_path)


def test_scaffold_suite_uses_name_in_variable_and_slug(tmp_path):
    scaffold("ai_content_summary", recipe="stubbed", root=tmp_path)
    suite_py = (tmp_path / "suites" / "ai_content_summary.py").read_text()
    # Variable bound on the module.
    assert "ai_content_summary_suite = suite(" in suite_py
    # name= argument used as the baseline directory slug.
    assert 'name="ai_content_summary"' in suite_py


def test_scaffold_eval_agent_recipe_specific_imports(tmp_path):
    """Each recipe's _eval_agent.py uses the right adapter / pattern."""
    sync_dir = tmp_path / "sync"
    async_dir = tmp_path / "async"
    stub_dir = tmp_path / "stub"
    scaffold("demo", recipe="sync-openai", root=sync_dir)
    scaffold("demo", recipe="async-openai", root=async_dir)
    scaffold("demo", recipe="stubbed", root=stub_dir)

    sync_src = (sync_dir / "suites" / "_eval_agent.py").read_text()
    async_src = (async_dir / "suites" / "_eval_agent.py").read_text()
    stub_src = (stub_dir / "suites" / "_eval_agent.py").read_text()

    assert "from agentprdiff.adapters.openai import" in sync_src
    assert "instrument_client" in sync_src

    assert "import asyncio" in async_src
    assert "asyncio.run" in async_src
    assert "instrument_client" not in async_src  # async path is manual

    assert "HELPER_NAME" in stub_src
    assert "_fake_helper" in stub_src


# ---------------------------------------------------------------------------
# CLI-level
# ---------------------------------------------------------------------------


def test_cli_scaffold_invokes_library(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["scaffold", "demo", "--dir", str(tmp_path)],
    )
    assert result.exit_code == 0, result.output
    assert "[new]" in result.output
    assert "Scaffolded 7 file(s)" in result.output
    assert (tmp_path / "suites" / "demo.py").exists()


def test_cli_scaffold_default_recipe_is_sync_openai(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["scaffold", "demo", "--dir", str(tmp_path)])
    assert result.exit_code == 0, result.output
    eval_agent = (tmp_path / "suites" / "_eval_agent.py").read_text()
    assert "instrument_client" in eval_agent


def test_cli_scaffold_invalid_name_exits_2(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        main, ["scaffold", "Bad-Name", "--dir", str(tmp_path)]
    )
    assert result.exit_code == 2, result.output
    assert "invalid name" in result.output.lower()


def test_cli_scaffold_unknown_recipe_rejected_by_click(tmp_path):
    """Click validates --recipe before we ever reach scaffold()."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "scaffold",
            "demo",
            "--dir",
            str(tmp_path),
            "--recipe",
            "not-real",
        ],
    )
    assert result.exit_code != 0
    # Click's standard "Invalid value for '--recipe'" message.
    assert "recipe" in result.output.lower()


def test_cli_scaffold_rerun_is_noop_with_skip_messages(tmp_path):
    runner = CliRunner()
    runner.invoke(main, ["scaffold", "demo", "--dir", str(tmp_path)])

    result = runner.invoke(main, ["scaffold", "demo", "--dir", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "[new]" not in result.output
    assert "[skip]" in result.output
    assert "Nothing scaffolded" in result.output


def test_cli_scaffold_then_list_works_on_generated_suite(tmp_path):
    """The generated suite file should be loadable by `agentprdiff check --list`.

    Adopters scaffold, look at what they got, and want to confirm the case
    list before wiring in the agent. The TODO-marker references in
    `_eval_agent.py` are inside function bodies, so module-level import is
    clean even before the user fills anything in. This test pins that
    contract — accidental template breakage (e.g. an undefined name at
    module scope) would surface here as a load failure.
    """
    runner = CliRunner()
    runner.invoke(main, ["scaffold", "demo", "--dir", str(tmp_path)])

    result = runner.invoke(
        main,
        [
            "--root",
            str(tmp_path / ".agentprdiff"),
            "check",
            str(tmp_path / "suites" / "demo.py"),
            "--list",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "demo" in result.output
    assert "happy_path" in result.output
