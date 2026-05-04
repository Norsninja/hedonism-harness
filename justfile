default:
    @just --list

install:
    uv sync --extra dev

test:
    uv run pytest

test-fast:
    uv run pytest -m "not slow"

test-determinism:
    uv run pytest -m determinism

smoke:
    uv run python scripts/core_smoke_test.py

ci:
    uv run ruff check .
    uv run ruff format --check .
    uv run pytest
    uv run python scripts/core_smoke_test.py

lint:
    uv run ruff check .

format:
    uv run ruff format .

fix:
    uv run ruff check --fix .
    uv run ruff format .

typecheck:
    @echo "mypy not yet wired — see §26.9. Run 'just typecheck' once core types settle."

precommit-install:
    uv run pre-commit install
