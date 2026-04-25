# Changelog

All notable changes to `agentprdiff` are documented in this file. Originally
prototyped under the name `tracediff`; renamed before first public release.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-04-22

Initial public release.

### Added

- Core `Suite` / `Case` / `Trace` model for defining agent regression tests.
- Deterministic graders: `contains`, `contains_any`, `regex_match`, `tool_called`,
  `tool_sequence`, `output_length_lt`, `latency_lt_ms`, `cost_lt_usd`,
  `no_tool_called`.
- Semantic grader (`semantic`) with a pluggable `judge` callable and built-in
  fake judge for CI environments without API keys.
- Baseline store (JSON files under `.agentprdiff/baselines/`) designed to be
  committed to version control.
- Trace diff engine producing a structured `TraceDelta` (assertion pass/fail
  changes, cost delta, latency delta, tool-call sequence changes, output
  change).
- CLI: `agentprdiff init`, `agentprdiff record`, `agentprdiff check`, `agentprdiff diff`.
- Rich-formatted terminal reporter and machine-readable JSON reporter for CI.
- Quickstart example with a mock agent that runs without any API keys.
- Pytest test suite covering graders, runner, differ, store, and CLI smoke.
- GitHub Actions CI workflow.

### Known limitations

- Only a manual instrumentation API for provider SDKs is shipped in 0.1.0.
  Drop-in wrappers for OpenAI / Anthropic / Vercel AI SDK are planned for 0.2.
- The semantic grader's built-in judge supports OpenAI and Anthropic via user-
  supplied API keys; hosted judge endpoints are not yet offered.
