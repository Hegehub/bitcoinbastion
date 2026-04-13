.PHONY: install test lint format up down run

install:
	pip install -e '.[dev]'

test:
	pytest -q

lint:
	ruff check app tests
	mypy app

format:
	black app tests

run:
	uvicorn app.main:app --reload

up:
	docker compose up -d

down:
	docker compose down

migrate:
	alembic upgrade head
