# Agents Guide

This document defines how agents work in this repository. General context: kmkkmk.

## Environment & Permissions
- Virtualenv is already configured and used for all work.
- Agents may install Python packages required for correct app operation.
- Agents may run shell commands related to running, developing, or maintaining the app.
- Agents may write and run temporary Python scripts for testing and development.
- GitHub access is available. Always ask for permission before pushing. If no repo exists, ask for project name and visibility (private/public) and then create it.

## Communication & Language
- Code, comments, and documentation are in English.
- Conversations with the user can be in Polish or English, depending on context.

## Product Source of Truth
- Main idea/brief: `README.md` (authoritative product overview and usage).
- Agent reference: `CLAUDE.md` (commands, architecture, component map).
- Supporting docs: `docs/CLI.md`, `docs/configuration.md`, `docs/product-ideas.md`.
- Draft vision: `docs_tmp/vision-refined.md` (Polish, treat as temporary; translate/move when stabilized).

## Workflow (Agile/Kanban)
- Roadmap: keep a high-level plan in `docs/product/current/roadmap.md`.
- Changelog: summarize recent changes, context, and decisions in `docs/changelog/<timestamp>.md`.
- Kanban:
  - TODO: plan tasks in `docs/kanban/todo/*.md` (one file per feature/value increment).
  - In Progress: move a file from TODO to `docs/kanban/inprogress/` when you start work.
  - Done: move from In Progress to `docs/kanban/done/*.md` when finished. One feature = one file; small improvements count as separate files.
  - Note: Create these folders if missing; prefer English for all permanent docs.

## Execution Protocol
- Start by creating/updating a TODO card with scope and acceptance criteria.
- When starting, move the card to In Progress and keep it updated.
- On completion, move the card to Done and add a concise changelog entry.
- Before moving to Done: run full test suite, format/lint as configured, update relevant docs, and prepare a commit.
- Commit changes locally per atomic task (one feature/improvement per commit) with a clear message referencing the Kanban card. Ask for permission before pushing to remote.

## Commit Messages
- Style: Conventional Commits.
  - Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `build`, `ci`, `revert`.
  - Format: `type(scope): short imperative summary` (max ~72 chars).
  - Breaking changes: add `!` in header or `BREAKING CHANGE:` in footer.
- Reference the Kanban card in the footer using the numeric prefix from the file name.
  - `Card-Id: 001` and a path reference: `Refs: docs/kanban/todo/001-cli-refactor-modularization.md`.
- Body (optional but recommended): what changed and why; wrap at ~72 chars.

Examples:
- `feat(cli): modularize generate/chat commands\n\nCard-Id: 001\nRefs: docs/kanban/todo/001-cli-refactor-modularization.md`
- `docs(architecture): add principles and link from roadmap\n\nCard-Id: 016\nRefs: docs/kanban/todo/016-docs-examples-providers-and-routing.md`

## Code Quality & Testing
- Maintain professional code quality; apply Single Responsibility Principle and YAGNI.
- Write unit tests for every feature.
- Maximum file size: 600 lines.
- Run tests with `python -m pytest tests -v` (see `TESTING.md` for details).
- If existing files exceed limits or violate rules, raise it and propose refactor.
- Prefer modular, extensible architecture with clear interfaces (e.g., provider adapters) to enable adding new backends (OpenAI, Groq, etc.) without breaking changes.
- Keep it simple: avoid heavy plugin frameworks; prefer small, focused modules and minimal, well-defined interfaces. Implement only necessary abstractions (YAGNI).
- Reference: see `docs/architecture-principles.md` for patterns, boundaries, and testing guidance.

## Tooling & Dependencies
- Use appropriate, vetted libraries; verify choices online before adoption.
- Care for developer experience (DX): proper tooling, linters/formatters, and helpful scripts where appropriate.
- Preferred tools (see `pyproject.toml`): `black`, `flake8`, `mypy`, `pytest`.
- Keep zero-config UX: avoid adding mandatory external services for core flows.
- Keep dependencies lean; avoid complex plugin systems unless clearly justified.
- Pre-commit hooks: configured in `.pre-commit-config.yaml` (black, ruff, file length check, commit-msg validation).
- Setup locally:
  - `pip install -r requirements-dev.txt`
  - `pre-commit install`
  - `pre-commit install --hook-type commit-msg`
  - Optional first run on entire repo: `pre-commit run --all-files`

## Questions & Assumptions
- When in doubt, ask product and logistical questions before proceeding.
