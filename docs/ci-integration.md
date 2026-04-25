# CI integration

`agentprdiff check` returns exit code `0` when all cases pass and no case
regressed against the baseline, and exit code `1` otherwise. That is the
whole integration story — drop it into any CI.

Below are recipes for the common systems.

## GitHub Actions

```yaml
# .github/workflows/agents.yml
name: agent-regression
on:
  pull_request:
  push:
    branches: [main]

jobs:
  agentprdiff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev]"
      - name: run regression tests
        env:
          # Only set if you use the semantic grader with a real judge.
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: agentprdiff check suites/*.py --json-out artifacts/agentprdiff.json
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: agentprdiff-report
          path: artifacts/
```

If you don't want to spend money on a real semantic judge in every PR,
leave the key unset — the semantic grader will fall back to `fake_judge`,
which matches keywords and is good enough for rough smoke-testing.

## GitLab CI

```yaml
agentprdiff:
  image: python:3.11
  script:
    - pip install -e ".[dev]"
    - agentprdiff check suites/*.py --json-out agentprdiff.json
  artifacts:
    when: always
    paths: [agentprdiff.json]
```

## CircleCI

```yaml
version: 2.1
jobs:
  agentprdiff:
    docker: [{ image: cimg/python:3.11 }]
    steps:
      - checkout
      - run: pip install -e ".[dev]"
      - run: agentprdiff check suites/*.py --json-out /tmp/agentprdiff.json
      - store_artifacts: { path: /tmp/agentprdiff.json }
```

## Buildkite

```yaml
steps:
  - label: ":robot: agentprdiff"
    command: |
      pip install -e ".[dev]"
      agentprdiff check suites/*.py --json-out agentprdiff.json
    artifact_paths: ["agentprdiff.json"]
```

## Reviewing a regression in a pull request

1. `agentprdiff check` prints the failing cases and a unified diff of the
   agent output for each regression, directly in the CI log.
2. The JSON artifact (`--json-out`) contains the full structured delta —
   every grader's pass/fail state, cost delta, latency delta, tool-call
   sequence change. Point your dashboarding at it if you care.
3. If the regression is **intentional**, the PR author runs
   `agentprdiff record suites/*.py` locally and commits the updated
   `.agentprdiff/baselines/` diff. Reviewers see the new baseline in the
   same PR — a first-class audit trail of "how the agent changed".

## Scheduled runs

`agentprdiff check` is idempotent and cheap when you use deterministic
graders, so it's reasonable to run it on a cron for drift detection
even when code hasn't changed — upstream models themselves can drift.

```yaml
on:
  schedule:
    - cron: "0 */6 * * *"   # every 6 hours
```
