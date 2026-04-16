.PHONY: install install-dev test test-contract test-integration lint format up down run dev worker bot migrate alembic-repro ci-smoke

install:
	python -m pip install -e .

install-dev:
	python -m pip install -e '.[dev]'

test: install-dev
	python -m pytest -q

test-contract: install-dev
	python -m pytest -q tests/contract

test-integration: install-dev
	python -m pytest -q tests/integration

lint:
	python -m ruff check app tests
	python -m mypy app

format:
	python -m black app tests

run:
	python -m uvicorn app.main:app --reload

dev: run

up:
	docker compose up -d --build

down:
	docker compose down

migrate:
	python -m alembic upgrade head

worker:
	python -m celery -A app.tasks.celery_app.celery_app worker --loglevel=info

bot:
	python -m app.bot.runner


alembic-repro:
	bash scripts/check_alembic_reproducibility.sh

ci-smoke: install-dev
	python -m alembic upgrade head
	bash scripts/check_alembic_reproducibility.sh
	python -m pytest -q tests/contract
