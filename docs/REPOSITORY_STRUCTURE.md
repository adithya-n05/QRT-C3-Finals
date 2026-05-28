# Repository Structure

This repository is organized for future models first: a short root instruction
file points to focused docs, and the executable harness is small enough to
trace quickly.

## Navigation Order

1. `AGENTS.md` - root map, safety rules, and common commands.
2. `docs/REPOSITORY_STRUCTURE.md` - this file; use it to locate ownership and
   decide where new files belong.
3. `docs/C3_GAME_PROTOCOL.md` - gameplay, API, scoring, and deadline rules.
4. `docs/COMPETITION_STRATEGY.md` - current tactical read and live playbook.
5. `docs/AGENT_FIRST_HARNESS.md` - why the repo is shaped this way and how to keep it
   legible.
6. `src/c3_harness/runner.py` - runtime loop and phase dispatch.
7. `src/c3_harness/telemetry.py` - local market event logging and replay capture.
8. `src/c3_harness/backtest.py` - historical replay and counterfactual scoring.
9. `tests/` - executable checks for strategy and harness behavior.
10. `scripts/` - stage-2 runbook helpers (live capture entrypoint).

## File Map

```text
.
├── AGENTS.md
├── README.md
├── .env.example
├── pyproject.toml
├── docs/
│   ├── AGENT_FIRST_HARNESS.md
│   ├── COMPETITION_STRATEGY.md
│   ├── C3_GAME_PROTOCOL.md
│   └── REPOSITORY_STRUCTURE.md
├── scripts/
│   └── run_stage2_capture.sh
├── src/
│   └── c3_harness/
│       ├── __init__.py
│       ├── __main__.py
│       ├── api.py
│       ├── backtest.py
│       ├── betting.py
│       ├── config.py
│       ├── runner.py
│       ├── strategy.py
│       └── telemetry.py
├── stage2_logs/
│   └── <run_id>/
│       └── stage2_events.ndjson
├── tools/
│   └── analyze_public_logs.py
└── tests/
    ├── test_betting.py
    ├── test_backtest.py
    ├── test_strategy.py
    └── test_telemetry.py
```

## Responsibilities

- `AGENTS.md`: concise context injected for coding agents. Keep it short and link
  deeper docs instead of embedding long explanations.
- `README.md`: human quickstart and verification commands.
- `.env.example`: non-secret environment variable template.
- `pyproject.toml`: Python project metadata.
- `docs/AGENT_FIRST_HARNESS.md`: agent-first design principles and guardrails.
- `docs/COMPETITION_STRATEGY.md`: opponent findings, broadcast policy, betting
  guidance, and live operational plan.
- `docs/C3_GAME_PROTOCOL.md`: local operational summary of the live C3 rules.
- `docs/REPOSITORY_STRUCTURE.md`: source of truth for file purpose and
  navigation.
- `src/c3_harness/api.py`: HTTP client wrapper for the C3 API.
- `src/c3_harness/betting.py`: parse and evaluate bet propositions.
- `src/c3_harness/config.py`: environment/config loading.
- `src/c3_harness/backtest.py`: replay and counterfactual scoring against logs.
- `src/c3_harness/telemetry.py`: market capture and decision audit stream.
- `src/c3_harness/runner.py`: polling loop and phase-specific submissions.
- `src/c3_harness/strategy.py`: policy and signal generation.
- `tools/analyze_public_logs.py`: read-only public log summarizer for opponent
  modeling.
- `tests/test_backtest.py`: backtest replay checks for the new round-history evaluator.
- `tests/test_betting.py`: betting parser and proposition checks.
- `tests/test_strategy.py`: strategy policy checks.
- `tests/test_telemetry.py`: logger event stream integrity checks.

## Where To Put New Work

- Add protocol parsing or API wrappers under `src/c3_harness/`.
- Add strategic decisions to `strategy.py` until the file becomes too large;
  then split by responsibility and update this map.
- Add tests in `tests/` that mirror the module under test.
- Add runbook scripts in `scripts/` for launch patterns used in live capture.
- Add design notes or operational runbooks in `docs/`.
- Keep temporary outputs in `stage2_logs/` and add to `.gitignore`.

## Model Instructions

- Start with the navigation order above before editing.
- Do not infer live API behavior from dashboard HTML when `/state`, `/logs`, or
  OpenAPI data is available.
- Prefer dry-run validation before live gameplay.
- After changing code, run:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

- If you add, remove, or repurpose files, update this document in the same
  change.
