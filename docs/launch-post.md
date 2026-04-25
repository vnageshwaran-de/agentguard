# Show HN: agentguard — guard your LLM agents in CI

*Draft for Hacker News / Reddit r/MachineLearning / X. Post on a Tuesday or Wednesday morning ET.*

---

**Title:** Show HN: Agentguard – snapshot tests that guard LLM agents against regressions in CI

Hi HN — I built agentguard (https://github.com/vnageshwaran-de/agentguard) because every team I've worked with that ships LLM agents has the same quiet failure mode: a model upgrade, a prompt tweak, or a vendor swap silently changes agent behavior in ways nobody notices until a customer complains.

The usual answers don't quite fit:

* Unit tests assume determinism. Agents aren't deterministic.
* Full LLM-as-judge eval pipelines (Langsmith, Braintrust, Humanloop) are powerful but expensive to run per-PR and require you to buy into their platform.
* Ad-hoc Jupyter notebooks for "let me run a few prompts and eyeball the output" don't live in CI.

Agentguard is the narrowest possible tool that solves *only* the CI-regression problem:

1. You write cases: `(input, list_of_assertions)`.
2. You run `agentguard record` once on a known-good agent — the trace (LLM calls, tool calls, output, cost, latency) is saved to `.agentguard/baselines/<suite>/<case>.json` and checked into git.
3. On every PR you run `agentguard check`. It re-runs each case, re-evaluates each assertion, diffs the new trace against the baseline, and exits 1 if anything regressed.

A few design choices that make it cheap to try:

* **10 batteries-included graders**, all deterministic except one: `contains`, `regex_match`, `tool_called`, `tool_sequence`, `no_tool_called`, `output_length_lt`, `latency_lt_ms`, `cost_lt_usd`, plus `semantic()` for LLM-as-judge with a pluggable `Judge` callable. If you set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`, the semantic grader calls that provider. If neither is set, it falls back to a deterministic `fake_judge` that keyword-matches — so CI stays green and free.
* **JSON baselines checked into git.** Reviewers see trace changes inline in pull requests. The audit trail for "how the agent's behavior changed" becomes a normal code review artifact.
* **Zero framework lock-in.** Your agent is any callable. Wrap it in `agentguard.suite(...)` and you're done. No inheritance, no subclasses, no decorators, no monkey-patching.
* **One happy path.** There is exactly one way to define a suite, one way to record, one way to check. The public API is ~10 names.

### The 10-line hello world

```python
from agentguard import case, suite
from agentguard.graders import contains, tool_called, latency_lt_ms, semantic
from my_agent import run

s = suite(name="billing", agent=run, cases=[
    case(name="refund", input="I want a refund for #1234",
         expect=[contains("refund"), tool_called("lookup_order"),
                 semantic("agent confirms refund"), latency_lt_ms(10_000)]),
])
```

```
$ agentguard record suite.py
$ agentguard check  suite.py   # exit 1 on regression
```

### What's it like to use?

The readme has a 60-second quickstart that runs in your terminal without any API keys (it uses a mock agent). Break the mock agent and watch agentguard point at the specific grader that flipped, the cost delta, the tool sequence that changed, and a unified diff of the output.

### Comparisons

* **DeepEval / Promptfoo:** great at evaluation; more framework than agentguard. If you want to run 10k cases and track an ELO, use them. If you just want `exit 1` in CI when today's PR breaks yesterday's behavior, agentguard is 50 lines of setup.
* **Langfuse / LangSmith:** great at observability on production traffic. Agentguard is the offline, pre-production, deterministic counterpart.
* **Jest snapshot tests / pytest-regressions:** closest analogue. Agentguard is those — but for agent traces specifically, with cost/latency/tool-sequence first-class.

### Status

0.1.0 — alpha. Core API is stable. Drop-in SDK wrappers for OpenAI / Anthropic / Vercel AI SDK are on the 0.2 roadmap. MIT license, Python 3.10+.

Would love feedback — especially from teams that have built their own in-house equivalent. The design decisions I've made (baselines-in-git, deterministic-first graders, semantic as one of ten rather than the only grader) are all load-bearing and I'm keen to hear where they break down.

Repo: https://github.com/vnageshwaran-de/agentguard
PyPI: `pip install agentguard`

— Vinoth
