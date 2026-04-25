"""Load `Suite` objects from user-provided Python files.

We deliberately keep this ultra-simple for v0.1: the user points at a python
file path (or module) and we import it; every module-level `Suite` instance
is a suite to run.
"""

from __future__ import annotations

import contextlib
import importlib.util
import sys
from pathlib import Path

from .core import Suite


def load_suites(path: str | Path) -> list[Suite]:
    """Import `path` and return every module-level `Suite` it defines."""
    p = Path(path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"no such file: {p}")
    if p.is_dir():
        raise IsADirectoryError(
            f"{p} is a directory; point at a .py file that defines Suites."
        )

    module_name = f"_agentprdiff_suite_{abs(hash(str(p)))}"
    spec = importlib.util.spec_from_file_location(module_name, p)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise ImportError(f"could not load suite file: {p}")
    module = importlib.util.module_from_spec(spec)
    # Ensure the file's own directory is importable (for relative helpers).
    sys.path.insert(0, str(p.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        with contextlib.suppress(ValueError):
            sys.path.remove(str(p.parent))

    suites = [v for v in vars(module).values() if isinstance(v, Suite)]
    if not suites:
        raise ValueError(
            f"{p} defines no module-level Suite objects. "
            "Use `from agentprdiff import suite` and bind the result to a variable."
        )
    return suites
