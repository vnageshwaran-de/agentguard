# Quickstart

```bash
pip install agentguard
```

## 1. Wrap your agent

Your agent can be any callable that takes an input and returns an output.
If you want `agentguard` to assert on tool calls, cost, or latency, return
a `(output, Trace)` tuple and record `LLMCall` / `ToolCall` objects on the
`Trace` as your agent runs.

```python
from agentguard import Trace, LLMCall, ToolCall

def my_agent(query: str) -> tuple[str, Trace]:
    trace = Trace(suite_name="", case_name="", input=query)

    # ... your code that calls a model ...
    response = anthropic_client.messages.create(...)
    trace.record_llm_call(LLMCall(
        provider="anthropic",
        model="claude-sonnet-4-6",
        prompt_tokens=response.usage.input_tokens,
        completion_tokens=response.usage.output_tokens,
        cost_usd=_cost(response.usage),
        latency_ms=elapsed_ms,
    ))

    # ... your tool calls ...
    trace.record_tool_call(ToolCall(name="lookup_order", arguments={...}))

    return final_text, trace
```

## 2. Write a suite

```python
# suite.py
from agentguard import case, suite
from agentguard.graders import contains, tool_called, latency_lt_ms, semantic

from my_agent import my_agent

billing = suite(
    name="billing",
    agent=my_agent,
    cases=[
        case(
            name="refund_happy_path",
            input="I want a refund for order #1234",
            expect=[
                contains("refund"),
                tool_called("lookup_order"),
                semantic("agent acknowledges the refund and explains next steps"),
                latency_lt_ms(10_000),
            ],
        ),
    ],
)
```

## 3. Record baselines

```
$ agentguard init
$ agentguard record suite.py
```

Commit `.agentguard/baselines/` to your repo.

## 4. Check in CI

```
$ agentguard check suite.py
```

Exit 0 when everything passes. Exit 1 on regression.

## 5. Update baselines when behavior intentionally changes

When a PR genuinely improves agent behavior, re-record and commit the new
baseline so reviewers can see the before/after:

```
$ agentguard record suite.py
$ git diff .agentguard/baselines/
```
