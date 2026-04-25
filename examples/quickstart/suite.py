"""Quickstart agentguard suite.

Run with::

    agentguard record examples/quickstart/suite.py
    agentguard check  examples/quickstart/suite.py

Both commands work with zero API keys — this example uses a mock agent so
the whole loop is fast and deterministic.
"""

from __future__ import annotations

from agentguard import case, suite
from agentguard.graders import (
    contains,
    cost_lt_usd,
    latency_lt_ms,
    no_tool_called,
    output_length_lt,
    semantic,
    tool_called,
)

from agent import support_agent  # type: ignore[import-not-found]


support = suite(
    name="customer_support",
    agent=support_agent,
    description="End-to-end regression tests for the support agent.",
    cases=[
        case(
            name="refund_happy_path",
            input="I want a refund for order #1234",
            expect=[
                contains("refund"),
                tool_called("lookup_order"),
                semantic("agent acknowledges the refund and explains the timeline"),
                latency_lt_ms(5_000),
                cost_lt_usd(0.01),
            ],
        ),
        case(
            name="non_refundable_order",
            input="I want a refund for order #9999",
            expect=[
                contains("agent"),
                tool_called("lookup_order"),
                output_length_lt(400),
            ],
        ),
        case(
            name="policy_question_no_tools",
            input="What is your return policy?",
            expect=[
                contains("30 days"),
                no_tool_called("lookup_order"),
                semantic("agent explains the return policy"),
            ],
        ),
        case(
            name="missing_order_number",
            input="Something is wrong with my order",
            expect=[
                contains("order number"),
                no_tool_called("lookup_order"),
            ],
        ),
    ],
)
