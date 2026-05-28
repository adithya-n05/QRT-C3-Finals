# QRT.C3 Agent Harness

Basic agent-first harness for the QRT.C3 Grand Final game server at
`https://c3.qwerty.technology`.

The repository follows the harness-engineering idea that future agents need a
map, executable feedback loops, and repository-local context. Start with
[AGENTS.md](AGENTS.md), then follow the docs in `docs/`.

## Quick Start

```bash
export C3_GAME_KEY="<team-game-key>"
PYTHONPATH=src python -m c3_harness.runner --once
```

The harness is dry-run by default. It will read state and print the submission
it would make. To submit to the live game:

```bash
PYTHONPATH=src python -m c3_harness.runner --live
```

## Verify

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

## Public Log Analysis

```bash
python tools/analyze_public_logs.py
```

## Logging and Round-2 Backtest

Enable logging on live or dry-run runs:

```bash
PYTHONPATH=src C3_GAME_KEY=... python -m c3_harness.runner --live --log-market
```

### Round-2 capture (one command)

```bash
export C3_GAME_KEY="bagel-fancy-jade"
./scripts/run_stage2_capture.sh
```

This starts a live polling loop immediately with market logging enabled and writes
NDJSON into `stage2_logs/<run_id>/<run_name>_events.ndjson`.
Use extra flags to control runtime (`--max-loops`, `--once`) and `C3_POLL_INTERVAL_SECONDS`
for timing.

Run local replay on completed rounds:

```bash
PYTHONPATH=src python -m c3_harness.backtest --logs /path/to/logs.json --team-id "<team_id>"
```

## Documentation

- [docs/REPOSITORY_STRUCTURE.md](docs/REPOSITORY_STRUCTURE.md): file map and
  model navigation instructions.
- [docs/C3_GAME_PROTOCOL.md](docs/C3_GAME_PROTOCOL.md): local summary of the
  game protocol and scoring rules.
- [docs/COMPETITION_STRATEGY.md](docs/COMPETITION_STRATEGY.md): current
  opponent model, broadcast policy, and live playbook.
- [docs/BACKTEST_RESULTS.md](docs/BACKTEST_RESULTS.md): latest stored-log
  replay results.
- [docs/AGENT_FIRST_HARNESS.md](docs/AGENT_FIRST_HARNESS.md): design principles
  for keeping this repo useful to future coding agents.
