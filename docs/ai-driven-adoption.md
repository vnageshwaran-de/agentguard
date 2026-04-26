# Adopting agentprdiff with an AI coding assistant

This page is for the **human user** who wants Claude Code, Cursor, Aider, Copilot, or any agentic IDE to add `agentprdiff` to their codebase. It contains copy-paste prompt templates, a recommendation about which to use when, and tips for getting the AI agent to produce a good suite instead of a bland one.

If you are the AI agent itself, read [`AGENTS.md`](../AGENTS.md) at the repo root — that's the document you're meant to consume.

---

## TL;DR

Open your AI coding assistant in your project. Tell it to read `AGENTS.md` from the agentprdiff repo. Then issue **Level 2** below. The whole adoption takes 15–20 minutes including review checkpoints.

---

## Pre-prompt setup (do this once)

The richest setup is roughly 60 seconds:

1. Open the project in Claude Code / Cursor / Aider / Copilot Chat.
2. Tell the assistant to fetch and read `AGENTS.md` from agentprdiff:

   ```
   Before answering anything else, fetch and read
   https://github.com/vnageshwaran-de/agentprdiff/blob/main/AGENTS.md
   into your context. Acknowledge when done.
   ```

3. Wait for acknowledgement.

This step matters because most AI assistants' training data predates `agentprdiff`'s existence; without an explicit fetch they'll hallucinate the API. Pinning `AGENTS.md` at the start of the session ensures the agent works from current information.

If your assistant doesn't support web fetches, paste the contents of `AGENTS.md` directly into the chat instead. It's about 700 lines.

---

## Level 1 — minimum viable

Use this when you're agentprdiff-curious and want to see what a baseline integration looks like quickly. Good for projects with one or two tools and clear intent. Less good for nuanced agents — the AI agent has to invent your contracts.

```
Add agentprdiff to this repo. Read AGENTS.md from the agentprdiff
package (or fetch it from
https://github.com/vnageshwaran-de/agentprdiff/blob/main/AGENTS.md)
and follow it end-to-end.

When you reach Step 2 (propose cases), show me the table you fill in
and wait for my approval before writing any code.
```

What you'll review: a table of 5–10 proposed cases. You approve or adjust. The AI agent does the rest.

Time to result: ~15 minutes.

---

## Level 2 — recommended default

Use this for any real adoption. Two checkpoints add maybe 8 minutes of review and produce a substantially better suite.

```
Add agentprdiff to this repo. Follow AGENTS.md.

Before writing any code, do these in order:

1. Find the agent (Step 1 in AGENTS.md). Tell me the entry function,
   the system prompt, and the tool dispatch dict so I can confirm you
   found the right things.

2. Propose 5–10 cases (Step 2). For each case, write one sentence
   that names: the input, what the agent must do, what it must NOT
   do, and a rough cost/latency budget. Show me the list before
   writing the suite.

3. Once I approve the case list, execute Steps 3 through 7. Use the
   OpenAI-compatible adapter unless the agent visibly uses native
   Anthropic. Stub any tool with side effects.

4. After `agentprdiff record`, tell me explicitly whether any case
   failed during recording — those are real findings, not test bugs.

Don't modify any production code under <agent_module_path>. The
whole integration goes in a new suites/ folder.
```

Replace `<agent_module_path>` with the directory holding your production agent (e.g., `agent/`, `src/agent/`, `app/llm/`).

What you'll review: (a) a confirmation of which files the AI agent thinks contain your production agent, and (b) a proposed case list. You approve both before any code is written.

Time to result: ~20 minutes including review.

---

## Level 3 — contract-driven

Use this when your agent has had behavioral incidents you want to encode as "never let *this specific thing* regress again." Each row in the prompt becomes a tombstone.

```
Add agentprdiff to this repo. Follow AGENTS.md.

Here are the behaviors I care about — turn each into a case:

1. <input example>     → must call <tool>, must NOT call <tool>
2. <input example>     → must ask for clarification, no tool call
3. <input example>     → must finish in under <X>ms and cost under <$Y>
4. <input example>     → must NOT mention <forbidden topic>
5. <input example>     → must follow the tool sequence [tool_a, tool_b]

Wrap the agent using the OpenAI-compatible adapter. Stub <list of
tools that have side effects>. Do not modify production code.

After `agentprdiff record`, report:
- which cases passed,
- which cases failed during recording (these are real bugs, flag them),
- the per-case cost so I know what the suite costs to run in CI.
```

Time to write the prompt: ~15 minutes (the thinking is in the contract list).
Time to result after the prompt is sent: ~10 minutes.

This produces the highest-quality suite because the contract is hand-curated. Each case maps to a real concern instead of a generic one.

---

## Working with the AI agent through the flow

A few small habits that make adoption smoother.

**At the discovery checkpoint**, verify the AI agent found the right entry point. Some projects have multiple LLM call sites; the agent might find a development-only one or a deprecated one. Cross-check against where your `main.py` (or equivalent) actually dispatches.

**At the case-proposal checkpoint**, push back on cases that aren't useful. "I don't actually care about that behavior" is a valid response. The AI agent will sometimes propose a case for every tool because that's the symmetric thing to do; you might only care about three of them. Cull aggressively. A 5-case suite that catches real regressions is worth more than a 12-case suite that flaps.

**When `record` produces a failure on first run**, do not assume the suite is wrong. Read the failure carefully. In coursenotes-ai's first adoption, two cases failed on first record — both were real production bugs the existing pytest suite hadn't caught. The right move is usually (a) accept the current behavior as the recorded baseline if the issue is well-understood, or (b) fix the production agent in a separate PR before merging the suite. Don't loosen the assertion to make the test pass — that defeats the whole point.

**When `agentprdiff check` is non-deterministic across runs**, the first instinct is to set `temperature=0`. Don't. The suite should mirror production's actual non-determinism so it catches the regressions production users will see. Instead, broaden assertions: use `contains_any([...])` instead of `contains(...)`, use `tool_called` instead of asserting on tool arguments, use `tool_sequence` with `strict=False` instead of `strict=True`.

**Treat the AI agent as a junior who's read the manual.** It can execute the playbook precisely but it doesn't know what bit your team last quarter. The user (you) provides the institutional knowledge. The AI agent provides the implementation discipline. Both halves matter.

---

## What to do after the first adoption

Once you have a green suite committed, the maintenance pattern is:

When you make a prompt or model change → run `agentprdiff check` locally, see what flips, decide whether to fix or re-record. If re-recording, commit the new baselines as a separate commit so reviewers can `git diff` the trace JSONs.

When a customer reports a bug → write the reproducing input as a new case, record the (failing) baseline, fix the agent, re-record. The case is now a tombstone.

When you upgrade an SDK (e.g., bump `openai>=1.50` to `>=2.0`) → run `agentprdiff check`. SDK upgrades sometimes change client behavior in ways that affect what gets recorded. Re-record if everything still passes; investigate if not.

Every six months → cull cases that are no longer relevant. A case for a tool you removed is dead weight.

---

## Sample first session, transcribed

This is a slightly edited transcript of what a real first-adoption session looks like with Level 2:

> **Human:** Before answering anything else, fetch and read `https://github.com/vnageshwaran-de/agentprdiff/blob/main/AGENTS.md` into your context. Acknowledge when done.
>
> **Assistant:** I've read AGENTS.md. Ready.
>
> **Human:** Add agentprdiff to this repo. Follow AGENTS.md. [Level 2 prompt as above…]
>
> **Assistant:** I ran the discovery commands. The production agent appears to be `agent/agent.py:run_agent`. The system prompt is `SYSTEM_PROMPT` at line 87. The tool dispatch dict is `TOOL_MAP` at line 80, mapping four names to functions in `tools/ytdlp_tools.py`. All four tools have side effects (they shell out to yt-dlp). Confirm I found the right files?
>
> **Human:** Yes. Proceed.
>
> **Assistant:** Proposing 7 cases:
>
> 1. `youtube_playlist_routes_to_download_all` — input: a playlist URL with explicit download intent → must call `download_all_transcripts`, must NOT call `download_transcript`. Budget: cost < $0.005, latency < 30s.
> 2. … [six more rows]
>
> Confirm or adjust this list?
>
> **Human:** Add a case for "what's already downloaded for course X" — that should call `list_downloaded_transcripts` only, no downloads. Otherwise looks good.
>
> **Assistant:** Added. Proceeding with Steps 3–7.
>
> [10 minutes pass]
>
> **Assistant:** Done. 7 cases recorded. 5 passed during recording, 2 failed:
> - `metadata_query_uses_get_course_info_only` — the model called `download_all_transcripts` in addition to `get_course_info`. The case asserted `no_tool_called('download_all_transcripts')`. This is a real behavioral issue — the agent inconsistently routes metadata queries.
> - `missing_url_asks_for_one` — the model called `download_all_transcripts` despite no URL being provided. The case asserted no tool calls plus an "ask for URL" requirement. This is also a real behavioral issue.
>
> Both findings come from the same gap: the system prompt doesn't explicitly say "ask for URLs when missing" or "don't download for metadata queries." Recommendation: file a separate PR that tightens `SYSTEM_PROMPT` and re-records baselines after.

That's the typical shape — find issues, flag them, leave the fix for a follow-up so the suite-adoption PR stays focused.

---

## Summary card to keep open

```
1. Pre-prompt:  Tell the AI agent to fetch AGENTS.md.
2. Prompt:      Use Level 2 unless you have a strong reason for Level 1 or 3.
3. Checkpoint:  Confirm the agent found the right files.
4. Checkpoint:  Approve / adjust the proposed case list.
5. Wait:        Roughly 10 minutes for the AI agent to execute Steps 3–7.
6. Review:      If `record` flagged regressions, treat them as real bugs.
7. Commit:      The PR contains suites/, .agentprdiff/baselines/, and a workflow file. Nothing under your production agent path.
```

That's the playbook.
