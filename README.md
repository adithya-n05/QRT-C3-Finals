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

## Documentation

- [docs/REPOSITORY_STRUCTURE.md](docs/REPOSITORY_STRUCTURE.md): file map and
  model navigation instructions.
- [docs/C3_GAME_PROTOCOL.md](docs/C3_GAME_PROTOCOL.md): local summary of the
  game protocol and scoring rules.
- [docs/AGENT_FIRST_HARNESS.md](docs/AGENT_FIRST_HARNESS.md): design principles
  for keeping this repo useful to future coding agents.
