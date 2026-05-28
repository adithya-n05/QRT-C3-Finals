# Agent Navigation Map

This repository is set up as an agent-first harness for the QRT.C3 Grand Final
game server. Keep this file short: it is the table of contents, not the full
manual.

## Start Here

1. Read [docs/REPOSITORY_STRUCTURE.md](docs/REPOSITORY_STRUCTURE.md) for the
   file map and navigation rules.
2. Read [docs/C3_GAME_PROTOCOL.md](docs/C3_GAME_PROTOCOL.md) before changing
   gameplay behavior.
3. Read [docs/AGENT_FIRST_HARNESS.md](docs/AGENT_FIRST_HARNESS.md) before
   changing repo organization, docs, or harness boundaries.
4. For implementation work, start in `src/c3_harness/runner.py`, then follow
   imports into `api.py`, `strategy.py`, and `betting.py`.

## Safety Rules

- Do not commit secrets. Game keys belong in `C3_GAME_KEY` or a local `.env`,
  never in source or docs.
- The harness is dry-run by default. Live gameplay requires an explicit user
  request and the `--live` flag.
- Prefer authenticated `/state` for agent decisions. Use dashboard/logs only
  for human inspection or read-only analysis.
- Treat the live rules at `https://c3.qwerty.technology/docs/rules` and
  `https://c3.qwerty.technology/docs/api` as the source of truth if local docs
  drift.
- Keep future instructions discoverable through docs instead of expanding this
  file into a large manual.

## Common Commands

```bash
PYTHONPATH=src python -m c3_harness.runner --once
PYTHONPATH=src python -m c3_harness.runner --live
PYTHONPATH=src python -m unittest discover -s tests
```

Set `C3_GAME_KEY` before calling authenticated endpoints:

```bash
export C3_GAME_KEY="<team-game-key>"
```

Optional configuration:

```bash
export C3_BASE_URL="https://c3.qwerty.technology"
export C3_POLL_INTERVAL_SECONDS="0.35"
```

## Work Style

- Make small, verifiable changes.
- Add or update tests when modifying protocol parsing, betting logic, or
  strategy decisions.
- Update `docs/REPOSITORY_STRUCTURE.md` whenever files are added, removed, or
  repurposed.
- Update `docs/C3_GAME_PROTOCOL.md` when the live game docs change in a way
  that affects agent behavior.
