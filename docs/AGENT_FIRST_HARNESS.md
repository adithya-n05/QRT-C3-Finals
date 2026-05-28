# Agent-First Harness

This setup follows the harness-engineering guidance from OpenAI's article,
`Harness engineering: leveraging Codex in an agent-first world`:
`https://openai.com/index/harness-engineering/`.

The local interpretation is simple: make the repository itself carry enough
context, tooling, and verification for a future model to do useful work without
external chat history.

## Principles

1. `AGENTS.md` is a map, not a manual.
2. Detailed knowledge lives in focused `docs/` files.
3. Runtime behavior is executable through a small harness.
4. Safety defaults are encoded in code, not just prose.
5. Tests cover protocol helpers and strategy assumptions.

## Harness Boundaries

The harness is intentionally thin:

- `api.py` knows HTTP mechanics.
- `runner.py` knows phase dispatch and live/dry-run behavior.
- `strategy.py` knows how to choose joins, bets, broadcasts, and actions.
- `betting.py` knows the proposition grammar.

This keeps future agents from needing to inspect unrelated files for common
changes.

## Safety Defaults

- Dry-run is the default.
- Live mutation requires `--live`.
- The game key is read from `C3_GAME_KEY`.
- No OpenAI API key is required by this basic harness.
- The agent must submit actions for every known opponent to avoid avoidable
  missing-action penalties.

## Feedback Loop

Use this loop for changes:

1. Read `AGENTS.md`.
2. Follow the file map in `docs/REPOSITORY_STRUCTURE.md`.
3. Change the smallest relevant module.
4. Add/update tests.
5. Run:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

6. Update docs when structure or protocol assumptions change.

## Future Improvements

- Add persistent opponent modeling from `/logs`.
- Add richer betting calibration from historical action counts.
- Add an evaluation harness that replays logged rounds against candidate
  strategies.
- Add structured run logs for every live submission and response.
