# Simple task runner for the CompileX project.

PYTHON ?= python
APP_ENTRY ?= gui/interface.py

.PHONY: run gui test test-lexer test-parser test-semantic test-tac clean help

run: gui

# Launch the GUI entrypoint when available.
gui:
	@if [ -f "$(APP_ENTRY)" ]; then \
		$(PYTHON) "$(APP_ENTRY)"; \
	else \
		echo "GUI entrypoint not found: $(APP_ENTRY)"; \
		echo "Implement Phase 7 (GUI Development) to enable this command."; \
		exit 1; \
	fi

# Run all project tests.
test:
	$(PYTHON) -m pytest -q

# Run lexer tests only (Phase 2).
test-lexer:
	$(PYTHON) -m pytest -q tests/test_lexer.py

# Run parser tests only (Phase 3).
test-parser:
	$(PYTHON) -m pytest -q tests/test_parser.py

# Run semantic analyzer tests only (Phase 4).
test-semantic:
	$(PYTHON) -m pytest -q tests/test_semantic.py

# Run TAC generator tests only (Phase 5).
test-tac:
	$(PYTHON) -m pytest -q tests/test_tac_generator.py

# Remove temporary Python cache files.
clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Show available make commands.
help:
	@echo "Available commands:"
	@echo "  make run         - Run the main application (alias for gui)"
	@echo "  make gui         - Launch the GUI entrypoint"
	@echo "  make test        - Run all tests"
	@echo "  make test-lexer  - Run lexer tests only"
	@echo "  make test-parser - Run parser tests only"
	@echo "  make test-semantic - Run semantic analyzer tests only"
	@echo "  make test-tac    - Run TAC generator tests only"
	@echo "  make clean       - Remove __pycache__ and *.pyc files"
	@echo "  make help        - Show this help message"
