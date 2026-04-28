"""Narrow a list of suites to a subset of cases by name pattern.

Used by `agentprdiff record` and `agentprdiff check` to support `--case` and
`--skip` filters. Patterns are matched against case names (or `suite:case`
when the user qualifies them) using glob or substring rules:

* If the pattern contains a glob metacharacter (`*`, `?`, `[`), it is matched
  with :func:`fnmatch.fnmatchcase` (case-insensitive).
* Otherwise it is treated as a case-insensitive substring.

A leading ``~`` (or ``!``) negates the pattern, so ``--case ~slow`` is a
shorthand for ``--skip slow``. Comma-separated values are split into multiple
patterns: ``--case refund,policy`` is equivalent to ``--case refund --case
policy``.

The resulting :func:`apply_filter` returns *new* :class:`Suite` instances with
their ``cases`` lists narrowed; suites that end up empty are dropped from the
result so the caller can detect a zero-match selection by checking whether the
returned list is empty.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass

from .core import Suite


@dataclass(frozen=True)
class Pattern:
    """A single parsed `--case` / `--skip` pattern."""

    raw: str
    text: str
    suite: str | None
    negate: bool

    @classmethod
    def parse(cls, raw: str) -> Pattern:
        text = raw.strip()
        negate = False
        if text.startswith(("~", "!")):
            negate = True
            text = text[1:].lstrip()
        suite: str | None = None
        # Allow `suite:case` qualification. We pick `:` over `/` because file
        # paths in shells with `/` are easier to mis-tab-complete.
        if ":" in text:
            suite, text = text.split(":", 1)
            suite = suite.strip() or None
            text = text.strip()
        return cls(raw=raw, text=text, suite=suite, negate=negate)

    def matches(self, suite_name: str, case_name: str) -> bool:
        """True if (suite_name, case_name) matches this pattern.

        Negation is *not* applied here — callers in :func:`apply_filter` use
        the ``negate`` flag to decide whether a match means include or
        exclude.
        """
        if self.suite is not None and not _match_one(self.suite, suite_name):
            return False
        return _match_one(self.text, case_name)


def parse_patterns(values: list[str]) -> list[Pattern]:
    """Parse a list of CLI option values into :class:`Pattern` objects.

    Each value may itself be a comma-separated list — Click's ``multiple=True``
    gives us repeated flags, and we additionally split on commas so users can
    say ``--case a,b`` instead of ``--case a --case b``.
    """
    out: list[Pattern] = []
    for raw in values:
        for piece in raw.split(","):
            piece = piece.strip()
            if piece:
                out.append(Pattern.parse(piece))
    return out


def apply_filter(
    suites: list[Suite],
    *,
    include: list[Pattern],
    exclude: list[Pattern],
) -> list[Suite]:
    """Narrow ``suites`` to cases matching the given filters.

    Rules:

    * If ``include`` contains any positive patterns, a case is kept only if
      it matches at least one of them.
    * Negative patterns inside ``include`` (those with ``~``) are merged with
      ``exclude`` and treated as unconditional drops.
    * Suites whose cases are all filtered out are removed from the result.

    The returned suites are fresh instances — the originals are not mutated.
    """
    pos = [p for p in include if not p.negate]
    neg = [p for p in include if p.negate] + list(exclude)

    out: list[Suite] = []
    for s in suites:
        kept = []
        for c in s.cases:
            if pos and not any(p.matches(s.name, c.name) for p in pos):
                continue
            if any(p.matches(s.name, c.name) for p in neg):
                continue
            kept.append(c)
        if kept:
            out.append(Suite(name=s.name, agent=s.agent, cases=kept, description=s.description))
    return out


def _match_one(pat: str, value: str) -> bool:
    if not pat:
        return True
    pat_l = pat.lower()
    val_l = value.lower()
    if any(c in pat for c in "*?["):
        return fnmatch.fnmatchcase(val_l, pat_l)
    return pat_l in val_l
