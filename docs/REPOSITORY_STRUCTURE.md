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
5. `docs/AGENT_FIRST_HARNESS.md` - why the repo is shaped this way and how to
   keep it legible.
6. `src/c3_harness/runner.py` - runtime loop and phase dispatch.
7. `tests/` - executable checks for protocol helpers and strategy behavior.

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
├── src/
│   └── c3_harness/
│       ├── __init__.py
│       ├── __main__.py
│       ├── api.py
│       ├── betting.py
│       ├── config.py
│       ├── runner.py
│       └── strategy.py
└── tests/
    ├── test_betting.py
    └── test_strategy.py
```

## Responsibilities

- `AGENTS.md`: concise context injected for coding agents. Keep it short and
  link deeper docs instead of embedding long explanations.
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
- `src/c3_harness/runner.py`: polling loop and phase-specific submissions.
- `src/c3_harness/strategy.py`: basic deterministic policy.
- `tests/`: standard-library `unittest` checks.

## Where To Put New Work

- Add protocol parsing or API wrappers under `src/c3_harness/`.
- Add strategic decisions to `strategy.py` until the file becomes too large;
  then split by responsibility and update this map.
- Add tests in `tests/` that mirror the module under test.
- Add design notes or operational runbooks in `docs/`.
- Put temporary local output under `output/` only when useful for inspection.

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
