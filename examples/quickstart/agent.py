"""A tiny mock agent used by the quickstart.

The real `agentprdiff` workflow is:

1. Your agent does its thing (calling OpenAI / Anthropic / whatever).
2. You instrument it: record `LLMCall` and `ToolCall` objects onto a `Trace`.
3. Return `(output, trace)` from your agent function.

We mock out steps 1–3 so the quickstart runs in CI with no API keys.
"""

from __future__ import annotations

from agentprdiff import LLMCall, ToolCall, Trace


ORDERS: dict[str, dict] = {
    "1234": {"amount_usd": 89.00, "status": "delivered", "refundable": True},
    "9999": {"amount_usd": 12.50, "status": "shipped", "refundable": False},
}


def lookup_order(order_id: str) -> dict | None:
    return ORDERS.get(order_id)


def support_agent(query: str) -> tuple[str, Trace]:
    """A stand-in customer-support agent.

    Deterministic, fully self-contained, no network. Produces a Trace with
    realistic-looking LLM and tool invocations so assertions have something
    to chew on.
    """
    trace = Trace(suite_name="", case_name="", input=query)

    # First "planner" LLM call.
    trace.record_llm_call(
        LLMCall(
            provider="mock",
            model="mock-sonnet-1",
            input_messages=[{"role": "user", "content": query}],
            output_text="I need to look up the order first.",
            prompt_tokens=18,
            completion_tokens=12,
            cost_usd=0.0002,
            latency_ms=180.0,
        )
    )

    # If the query mentions an order number, call lookup_order.
    import re

    m = re.search(r"#?(\d{4,})", query)
    order = None
    if m:
        order_id = m.group(1)
        trace.record_tool_call(
            ToolCall(name="lookup_order", arguments={"order_id": order_id}, latency_ms=8.0)
        )
        order = lookup_order(order_id)
        trace.tool_calls[-1].result = order

    # Final "responder" LLM call + output generation.
    if "refund" in query.lower() and order is not None:
        if order["refundable"]:
            output = (
                f"I can help with that. I've processed a refund of ${order['amount_usd']:.2f} "
                f"for your order. You'll see it back on your card in 3–5 business days."
            )
        else:
            output = (
                f"I looked up your order but it isn't refundable at this stage "
                f"(status: {order['status']}). I can connect you with a human agent."
            )
    elif "policy" in query.lower():
        output = (
            "Our return policy lets you return most items within 30 days of delivery "
            "for a full refund. Some exclusions apply — see our FAQ."
        )
    else:
        output = "Happy to help — could you share your order number?"

    trace.record_llm_call(
        LLMCall(
            provider="mock",
            model="mock-sonnet-1",
            input_messages=[{"role": "user", "content": query}],
            output_text=output,
            prompt_tokens=60,
            completion_tokens=len(output.split()),
            cost_usd=0.0008,
            latency_ms=420.0,
        )
    )

    return output, trace
