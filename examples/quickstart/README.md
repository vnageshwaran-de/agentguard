# agentprdiff quickstart

A minimal, runnable example. No API keys required.

```bash
# from the repo root:
pip install -e .
cd examples/quickstart

agentprdiff init
agentprdiff record suite.py   # records baselines for every case
agentprdiff check  suite.py   # re-runs every case, diffs against the baseline
```

The first `check` after `record` should exit 0 with all cases passing. Now
edit `agent.py` — change the refund wording or remove the `lookup_order`
tool call for a particular input — and re-run `agentprdiff check`. You'll see
the specific grader that now fails, a cost and latency delta, and a unified
diff of the output.

That's the whole loop. Swap `support_agent` for whatever production agent
you want to guard.
