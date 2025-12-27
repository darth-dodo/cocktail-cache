.PHONY: install dev test test-cov lint format typecheck check clean docker-build docker-run compute-unlocks

# Dependencies
install:
	uv sync
	uv run pre-commit install

# Development
dev:
	uv run uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8888

# Testing
test:
	uv run pytest -v

test-cov:
	uv run pytest --cov=src --cov-report=term-missing --cov-report=html

# Code Quality
lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests
	uv run ruff check --fix src tests

typecheck:
	uv run mypy src

check: lint typecheck test

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -f .coverage
	rm -rf .mypy_cache

# Docker
docker-build:
	docker build -t cocktail-cache .

docker-run:
	docker run -p 8888:8888 --env-file .env cocktail-cache

# Scripts
compute-unlocks:
	uv run python scripts/compute_unlock_scores.py
