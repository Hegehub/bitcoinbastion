 .PHONY: install install-dev test test-contract test-integration test-unit lint format up down up-prod run dev worker bot migrate alembic-repro alembic-roundtrip model-migration-coverage schema-runtime-parity db-schema-parity docs-truthfulness migration-smoke ci-smoke ci-release-gates compose-smoke postgres-migration-smoke postgres-schema-parity release-evidence

install:
	python -m pip install -e .

install-dev:
	python -m pip install -e '.[dev]'

test: install-dev
	python -m pytest -q

test-unit: install-dev
	python -m pytest -q tests/unit

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
	docker compose --env-file .env up -d --build

up-prod:
	ENVIRONMENT=prod docker compose --env-file .env up -d --build

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

alembic-roundtrip:
	python -m alembic downgrade base
	python -m alembic upgrade head

model-migration-coverage:
	python scripts/check_model_migration_coverage.py

schema-runtime-parity:
	python scripts/check_schema_runtime_parity.py

db-schema-parity:
	python scripts/check_schema_runtime_parity.py

docs-truthfulness:
	python scripts/check_docs_truthfulness.py

migration-smoke:
	python -m pytest -q tests/unit/test_migration_reproducibility.py

ci-smoke: install-dev
	python -m alembic upgrade head
	python -m alembic downgrade base
	python -m alembic upgrade head
	bash scripts/check_alembic_reproducibility.sh
	python -m pytest -q tests/unit/test_migration_reproducibility.py
	python scripts/check_model_migration_coverage.py
	python scripts/check_schema_runtime_parity.py
	python scripts/check_docs_truthfulness.py
	python -m pytest -q tests/contract

ci-release-gates: install-dev
	rm -f bitcoin_bastion.db
	python -m alembic upgrade head
	python -m alembic downgrade base
	python -m alembic upgrade head
	bash scripts/check_alembic_reproducibility.sh
	python -m pytest -q tests/unit/test_migration_reproducibility.py
	python scripts/check_model_migration_coverage.py
	python scripts/check_schema_runtime_parity.py
	python scripts/check_docs_truthfulness.py

compose-smoke:
	docker compose config >/dev/null



postgres-migration-smoke:
	python scripts/run_postgres_migration_smoke.py

postgres-schema-parity:
	python scripts/check_postgres_schema_parity.py

release-evidence:
	python scripts/collect_release_evidence.py
