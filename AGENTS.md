# Repository Guidelines

## Project Structure & Module Organization

This repository is currently a clean starter repo with no source tree committed yet. As code is added, keep the layout predictable:

- `src/` for application and library code.
- `tests/` for automated tests, mirroring `src/` where practical.
- `data/` for small sample inputs or fixtures that are safe to commit.
- `notebooks/` for exploratory analysis only; move reusable logic into `src/`.
- `docs/` for design notes, challenge writeups, and usage instructions.

Avoid committing generated artifacts, large datasets, virtual environments, caches, or local editor settings.

## Build, Test, and Development Commands

No build or test commands are defined yet. When tooling is introduced, document it in `README.md` and keep this guide in sync. Prefer simple, reproducible commands such as:

- `python -m pytest` to run Python tests.
- `python -m src.<module>` to run a Python entry point.
- `npm test` and `npm run build` if a Node project is added.
- `make test` or `make run` only if a `Makefile` exists and wraps the canonical commands.

## Coding Style & Naming Conventions

Use clear module boundaries and descriptive names. For Python, prefer 4-space indentation, `snake_case` for functions and files, `PascalCase` for classes, and type hints for public functions. For JavaScript or TypeScript, prefer 2-space indentation, `camelCase` for variables/functions, and `PascalCase` for classes/components.

Add formatting and linting tools with the first language stack, then commit their configuration files. Do not mix unrelated formatting changes with behavioral changes.

## Testing Guidelines

Place tests in `tests/` and name them after the behavior under test, for example `test_parser.py` or `pricing_engine.test.ts`. Cover edge cases, error paths, and any challenge-specific scoring logic. New features should include tests unless the change is purely documentation or configuration.

## Commit & Pull Request Guidelines

There is no existing commit history to infer conventions from. Use concise, imperative commit messages, for example `Add parser for market data` or `Document setup workflow`.

Pull requests should include a short description, the commands run to verify the change, and any relevant screenshots or output for user-facing behavior. Link issues or task notes when available, and call out known limitations explicitly.

## Agent-Specific Instructions

Before editing, inspect the current tree and avoid overwriting unrelated user changes. Keep changes scoped to the requested task, prefer repository-local conventions once they exist, and update this file when project structure or commands change.
