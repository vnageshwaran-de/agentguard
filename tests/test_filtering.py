"""Unit tests for the case-filter language used by `--case` / `--skip`."""

from __future__ import annotations

from agentprdiff import case, suite
from agentprdiff.filtering import Pattern, apply_filter, parse_patterns


def _agent(x):
    return f"echo:{x}"


def _make_suites():
    """Two suites with overlapping case-name shapes so qualifier rules show."""
    return [
        suite(
            name="customer_support",
            agent=_agent,
            cases=[
                case(name="refund_happy_path", input="r", expect=[]),
                case(name="non_refundable_order", input="n", expect=[]),
                case(name="policy_question_no_tools", input="p", expect=[]),
                case(name="missing_order_number", input="m", expect=[]),
            ],
        ),
        suite(
            name="billing",
            agent=_agent,
            cases=[
                case(name="refund_via_gateway", input="g", expect=[]),
                case(name="invoice_lookup", input="i", expect=[]),
            ],
        ),
    ]


# --------------------------------------------------------------------- parse


def test_parse_plain():
    [p] = parse_patterns(["refund"])
    assert p == Pattern(raw="refund", text="refund", suite=None, negate=False)


def test_parse_negation_tilde():
    [p] = parse_patterns(["~slow"])
    assert p.negate is True
    assert p.text == "slow"


def test_parse_negation_bang():
    [p] = parse_patterns(["!slow"])
    assert p.negate is True


def test_parse_qualifier():
    [p] = parse_patterns(["billing:refund*"])
    assert p.suite == "billing"
    assert p.text == "refund*"


def test_parse_negated_qualifier():
    [p] = parse_patterns(["~customer_support:slow"])
    assert p.negate is True
    assert p.suite == "customer_support"
    assert p.text == "slow"


def test_parse_comma_split():
    parsed = parse_patterns(["refund,policy"])
    assert [p.text for p in parsed] == ["refund", "policy"]


def test_parse_multiple_flags_and_commas():
    parsed = parse_patterns(["a,b", "c"])
    assert [p.text for p in parsed] == ["a", "b", "c"]


def test_parse_strips_whitespace_and_drops_empty():
    parsed = parse_patterns(["  refund , , policy  "])
    assert [p.text for p in parsed] == ["refund", "policy"]


# -------------------------------------------------------------------- match


def test_substring_match_case_insensitive():
    p = Pattern.parse("REFUND")
    assert p.matches("customer_support", "refund_happy_path") is True
    assert p.matches("customer_support", "policy_question_no_tools") is False


def test_glob_match_uses_fnmatch():
    p = Pattern.parse("*order*")
    assert p.matches("customer_support", "missing_order_number") is True
    assert p.matches("customer_support", "non_refundable_order") is True
    assert p.matches("customer_support", "refund_happy_path") is False


def test_qualifier_filters_by_suite():
    p = Pattern.parse("billing:refund*")
    assert p.matches("billing", "refund_via_gateway") is True
    assert p.matches("customer_support", "refund_happy_path") is False


# -------------------------------------------------------------------- apply


def test_apply_no_filters_returns_all():
    suites = _make_suites()
    out = apply_filter(suites, include=[], exclude=[])
    assert [s.name for s in out] == ["customer_support", "billing"]
    assert sum(len(s.cases) for s in out) == 6


def test_apply_substring_include():
    suites = _make_suites()
    out = apply_filter(suites, include=parse_patterns(["refund"]), exclude=[])
    flat = [(s.name, c.name) for s in out for c in s.cases]
    assert flat == [
        ("customer_support", "refund_happy_path"),
        ("customer_support", "non_refundable_order"),
        ("billing", "refund_via_gateway"),
    ]


def test_apply_glob_include():
    suites = _make_suites()
    out = apply_filter(suites, include=parse_patterns(["*order*"]), exclude=[])
    names = [c.name for s in out for c in s.cases]
    assert names == ["non_refundable_order", "missing_order_number"]


def test_apply_multiple_includes_are_or():
    suites = _make_suites()
    out = apply_filter(suites, include=parse_patterns(["refund", "policy"]), exclude=[])
    names = [c.name for s in out for c in s.cases]
    assert "refund_happy_path" in names
    assert "policy_question_no_tools" in names
    assert "invoice_lookup" not in names


def test_apply_skip_unconditional():
    suites = _make_suites()
    out = apply_filter(suites, include=[], exclude=parse_patterns(["policy"]))
    names = [c.name for s in out for c in s.cases]
    assert "policy_question_no_tools" not in names
    # everything else still present
    assert len(names) == 5


def test_apply_negation_inside_include():
    """`--case ~slow` should behave like `--skip slow`."""
    suites = _make_suites()
    out = apply_filter(suites, include=parse_patterns(["~policy"]), exclude=[])
    names = [c.name for s in out for c in s.cases]
    assert "policy_question_no_tools" not in names
    assert len(names) == 5


def test_apply_include_and_skip_combine():
    suites = _make_suites()
    out = apply_filter(
        suites,
        include=parse_patterns(["refund"]),
        exclude=parse_patterns(["gateway"]),
    )
    names = [c.name for s in out for c in s.cases]
    assert names == ["refund_happy_path", "non_refundable_order"]


def test_apply_qualifier_narrows_to_suite():
    suites = _make_suites()
    out = apply_filter(
        suites, include=parse_patterns(["billing:refund*"]), exclude=[]
    )
    assert [s.name for s in out] == ["billing"]
    assert [c.name for s in out for c in s.cases] == ["refund_via_gateway"]


def test_apply_drops_empty_suites():
    suites = _make_suites()
    out = apply_filter(suites, include=parse_patterns(["invoice"]), exclude=[])
    assert [s.name for s in out] == ["billing"]


def test_apply_zero_match_returns_empty_list():
    suites = _make_suites()
    out = apply_filter(suites, include=parse_patterns(["nonexistent"]), exclude=[])
    assert out == []


def test_apply_does_not_mutate_input():
    suites = _make_suites()
    before = [(s.name, [c.name for c in s.cases]) for s in suites]
    apply_filter(suites, include=parse_patterns(["refund"]), exclude=[])
    after = [(s.name, [c.name for c in s.cases]) for s in suites]
    assert before == after
