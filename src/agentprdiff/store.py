"""Baseline storage.

Baselines live in `.agentprdiff/baselines/<suite>/<case>.json` relative to the
project root. They are designed to be checked into git — reviewers should be
able to see them in pull requests and argue about changes.

Runs (every execution of `agentprdiff check`) are written under
`.agentprdiff/runs/` and are *not* checked in.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .core import Trace


class BaselineStore:
    """Filesystem-backed store for baseline traces."""

    def __init__(self, root: Path | str = ".agentprdiff") -> None:
        self.root = Path(root)

    # ------------------------------------------------------------------ paths

    @property
    def baselines_dir(self) -> Path:
        return self.root / "baselines"

    @property
    def runs_dir(self) -> Path:
        return self.root / "runs"

    def baseline_path(self, suite_name: str, case_name: str) -> Path:
        return self.baselines_dir / _safe(suite_name) / f"{_safe(case_name)}.json"

    def run_path(self, run_id: str, suite_name: str, case_name: str) -> Path:
        return self.runs_dir / run_id / _safe(suite_name) / f"{_safe(case_name)}.json"

    # ------------------------------------------------------------------ io

    def save_baseline(self, trace: Trace) -> Path:
        path = self.baseline_path(trace.suite_name, trace.case_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_dump_trace(trace), encoding="utf-8")
        return path

    def load_baseline(self, suite_name: str, case_name: str) -> Trace | None:
        path = self.baseline_path(suite_name, case_name)
        if not path.exists():
            return None
        return Trace.model_validate_json(path.read_text(encoding="utf-8"))

    def save_run_trace(self, run_id: str, trace: Trace) -> Path:
        path = self.run_path(run_id, trace.suite_name, trace.case_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_dump_trace(trace), encoding="utf-8")
        return path

    def ensure_initialized(self) -> None:
        self.baselines_dir.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        gitignore = self.root / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text("# Committed:   baselines/\n# Not committed: runs/\nruns/\n")

    def fresh_run_id(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _safe(name: str) -> str:
    """Make a case/suite name safe for use as a filename component."""
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in name) or "_"


def _dump_trace(trace: Trace) -> str:
    # pretty-printed JSON so git diffs are readable.
    return json.dumps(trace.model_dump(mode="json"), indent=2, sort_keys=False) + "\n"
