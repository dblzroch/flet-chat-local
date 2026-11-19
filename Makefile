.PHONY: run test lint fmt install

install:
	uv sync --dev

run:
	uv run flet-chat-local

test:
	uv run pytest

lint:
	uv run ruff check src tests
	uv run mypy src

fmt:
	uv run ruff format src tests
