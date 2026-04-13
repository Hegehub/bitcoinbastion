.PHONY: install test lint format up down run dev worker bot migrate

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

dev: run

up:
	docker compose up -d --build

down:
	docker compose down

migrate:
	alembic upgrade head

worker:
	celery -A app.tasks.celery_app.celery_app worker --loglevel=info

bot:
	python -m app.bot.runner
