# Contributing to agentguard

Thanks for your interest. This is a small, opinionated project; PRs that
fit the scope below are merged quickly.

## Scope

In scope:

* New deterministic graders (keep them dependency-free).
* New semantic-grader backends (pluggable `Judge` callables).
* SDK-specific instrumentation helpers under `agentguard/providers/`.
* CI reporters (JUnit XML, GitHub annotations, etc.).
* Bug fixes, test coverage, docs.

Out of scope for 0.1:

* A hosted service / SaaS.
* A new agent framework. `agentguard` intentionally does not care how your
  agent is built.
* Non-trace-based evaluation (pairwise preference, ELO). Different tool.

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check src tests
mypy src
```

The quickstart example under `examples/quickstart/` is also a CI smoke test:

```bash
cd examples/quickstart
agentguard record suite.py
agentguard check  suite.py   # should exit 0
```

## PR checklist

* Tests pass locally (`pytest`).
* Public API changes are reflected in `src/agentguard/__init__.py` and the
  README's "batteries-included graders" list.
* User-facing changes are noted in `CHANGELOG.md` under the next version.
* New graders include at least one passing and one failing test case.

## Code style

* Black-compatible formatting; `ruff` is the linter.
* Type hints on all public APIs.
* Prefer small, pure callables over classes.

## Releasing

Maintainers only:

```bash
# bump version in pyproject.toml, add CHANGELOG entry, tag
git tag v0.x.y && git push --tags
# GitHub Action publishes to PyPI on tag push.
```
