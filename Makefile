PYTHON ?= python
PYTEST ?= $(PYTHON) -m pytest
T ?=
X ?=
TIMEOUT ?= 60

.PHONY: help test test-fast test-collect test-core test-cli test-ui-cli test-providers test-diagnose test-timeout test-stacks smoke-tui
.DEFAULT_GOAL := help

help: ## Show help for common test targets
	@echo "Test shortcuts:"
	@echo "  make test [T=...] [X=...]      - run pytest with repo defaults"
	@echo "  make test-fast [T=...]          - quick run, no coverage"
	@echo "  make test-collect               - only discover tests"
	@echo "  make test-cli                   - CLI tests excluding UI"
	@echo "  make test-ui-cli                - only UI CLI tests"
	@echo "  make test-core                  - core tests"
	@echo "  make test-providers             - provider tests"
	@echo "  make test-diagnose              - verbose, durations"
	@echo "  make test-timeout [TIMEOUT=..]  - with timeout plugin (if installed)"
	@echo "  make test-stacks [TIMEOUT=..]   - dump stacks if stuck"
	@echo "  make smoke-tui [MODEL_ID=..]    - CLI-based TUI smoke (local-zeroconfig)"

test: ## Run full test suite (respects pytest.ini addopts)
	$(PYTEST) $(T) $(X)

test-fast: ## Run tests quickly without coverage/thresholds
	$(PYTEST) -q --no-cov $(T) $(X)

test-collect: ## Only collect tests
	$(PYTEST) --collect-only -q $(T)

test-core: ## Core tests
	$(PYTEST) -vv -s --no-cov tests/test_core.py $(T) $(X)

test-cli: ## CLI tests except UI CLI
	$(PYTEST) -vv -s --no-cov tests/test_*_cli.py --deselect tests/test_ui_cli.py $(T) $(X)

test-ui-cli: ## UI CLI tests (may build/launch TUI/Go)
	$(PYTEST) -vv -s --no-cov tests/test_ui_cli.py $(T) $(X)

test-providers: ## Provider tests
	$(PYTEST) -vv -s --no-cov tests/test_provider_*.py $(T) $(X)

test-diagnose: ## Verbose + durations to find slow/hanging tests
	$(PYTEST) -vv -s --no-cov --maxfail=1 --durations=10 $(T) $(X)

test-timeout: ## Add timeout watchdog (requires pytest-timeout)
	$(PYTEST) -vv -s --no-cov --timeout=$(TIMEOUT) $(T) $(X)

test-stacks: ## Dump stacks after TIMEOUT seconds via faulthandler
	$(PYTEST) -vv -s --no-cov --faulthandler-timeout=$(TIMEOUT) $(T) $(X)

smoke-tui: ## E2E smoke: providers e2e + set local + verify current
	$(PYTHON) scripts/smoke_tui.py
