Title: CLI refactor into modular subcommands (Done)

Outcome:
- Split `chi_llm/cli.py` into modular units under `chi_llm/cli_modules/` and `chi_llm/cli_main.py`.
- Kept entrypoint `chi_llm.cli:main` via a thin wrapper.
- Commands preserved: generate, chat, complete, ask, analyze, extract, summarize, translate, classify, template, rag, setup, models, interactive.
- `chi_llm/cli.py` reduced to 6 lines (<<600 rule met).
- All tests still pass (95/95) and coverage unchanged for core modules (~87%).

Scope:
- Split monolithic `chi_llm/cli.py` into small modules under `chi_llm/cli_modules/`.
- Keep UX and flags identical; maintain entrypoint `chi_llm.cli:main`.
- File size rule: ensure `chi_llm/cli.py` < 100 lines; parser and commands moved out.

Acceptance Criteria:
- `chi-llm --help` and subcommand helps render and match current options.
- All existing tests pass (`pytest -v`).
- No behavioral changes except internal structure.

Implementation Notes:
- New module `chi_llm/cli_main.py` exposes `build_parser()` and `main()`.
- Command groups in `chi_llm/cli_modules`: basic, data, templates, rag, models, interactive.
