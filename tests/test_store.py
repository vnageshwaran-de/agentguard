"""Tests for BaselineStore."""

from __future__ import annotations

from agentprdiff import Trace
from agentprdiff.store import BaselineStore


def test_save_and_load_baseline(tmp_path):
    store = BaselineStore(root=tmp_path / ".agentprdiff")
    store.ensure_initialized()
    t = Trace(suite_name="s", case_name="c", input="hi", output="hello")
    path = store.save_baseline(t)
    assert path.exists()

    loaded = store.load_baseline("s", "c")
    assert loaded is not None
    assert loaded.output == "hello"
    assert loaded.input == "hi"


def test_load_missing_returns_none(tmp_path):
    store = BaselineStore(root=tmp_path / ".agentprdiff")
    store.ensure_initialized()
    assert store.load_baseline("none", "none") is None


def test_names_with_unsafe_chars(tmp_path):
    store = BaselineStore(root=tmp_path / ".agentprdiff")
    store.ensure_initialized()
    t = Trace(suite_name="weird/name", case_name="case with spaces", input="x")
    path = store.save_baseline(t)
    assert path.exists()
    # The name should be filename-safe but the loaded trace carries the real
    # suite/case names.
    loaded = store.load_baseline("weird/name", "case with spaces")
    assert loaded is not None
    assert loaded.case_name == "case with spaces"


def test_ensure_initialized_writes_gitignore(tmp_path):
    store = BaselineStore(root=tmp_path / ".agentprdiff")
    store.ensure_initialized()
    gi = (tmp_path / ".agentprdiff" / ".gitignore").read_text()
    assert "runs/" in gi
