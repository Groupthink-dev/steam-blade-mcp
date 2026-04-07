.PHONY: dev test lint format clean install-dev

dev:
	uv run steam-blade-mcp

install-dev:
	uv sync --dev

test:
	uv run pytest -v

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

clean:
	rm -rf .venv __pycache__ src/steam_blade_mcp/__pycache__ tests/__pycache__ .pytest_cache .ruff_cache
