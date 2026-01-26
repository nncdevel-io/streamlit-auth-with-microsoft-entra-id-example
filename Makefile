.PHONY: install install-dev run test test-cov coverage lint type-check check docs docs-serve clean help

# Default target
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  install      Install dependencies"
	@echo "  install-dev  Install dependencies with dev tools"
	@echo "  run          Run Streamlit application"
	@echo "  test         Run tests"
	@echo "  test-cov     Run tests with coverage report"
	@echo "  coverage     Generate HTML coverage report"
	@echo "  lint         Run ruff linter"
	@echo "  type-check   Run mypy type checker"
	@echo "  check        Run lint and type-check"
	@echo "  docs         Generate API documentation with Sphinx"
	@echo "  docs-serve   Serve API documentation at http://localhost:8000"
	@echo "  clean        Remove cache files"
	@echo "  help         Show this help message"

# Install dependencies
install:
	uv sync

# Install with dev dependencies
install-dev:
	uv sync --dev --extra docs

# Run the application
run:
	uv run streamlit run src/entra_id_auth_example/app.py

# Run tests
test:
	uv run pytest

# Run tests with coverage
test-cov:
	uv run pytest --cov --cov-report=term-missing

# Generate HTML coverage report
coverage:
	uv run pytest --cov --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

# Run linter
lint:
	uv run ruff check .

# Run type checker
type-check:
	uv run mypy src

# Run all checks
check: lint type-check

# Generate documentation
docs:
	uv run sphinx-build -b html api-docs api-docs/_build/html
	@echo "Documentation generated in api-docs/_build/html/index.html"

# Serve documentation
docs-serve: docs
	@echo "Serving documentation at http://localhost:8000"
	cd api-docs/_build/html && uv run python -m http.server 8000

# Clean cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	rm -rf api-docs/_build 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
