 .PHONY: install install-dev test test-contract test-integration test-unit lint format up down up-prod run dev worker bot migrate alembic-repro alembic-roundtrip model-migration-coverage schema-runtime-parity db-schema-parity docs-truthfulness migration-smoke ci-smoke ci-release-gates compose-smoke postgres-migration-smoke postgres-schema-parity release-evidence k8s-render-staging k8s-render-production k8s-apply-staging k8s-apply-production k8s-status k8s-rollback-notes k8s-run-migration k8s-run-postgres-migration-smoke k8s-run-postgres-schema-parity k8s-run-release-evidence k8s-collect-evidence-artifacts

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


k8s-render-staging:
	kubectl kustomize deploy/kubernetes/overlays/staging

k8s-render-production:
	kubectl kustomize deploy/kubernetes/overlays/production

k8s-apply-staging:
	kubectl apply -k deploy/kubernetes/overlays/staging

k8s-apply-production:
	kubectl apply -k deploy/kubernetes/overlays/production

k8s-status:
	kubectl -n bitcoin-bastion get deploy,po,svc,ingress,pdb

k8s-rollback-notes:
	@echo "Rollback notes: pin last known-good image digest, re-apply previous overlay revision, and re-run health/readiness/recovery-check/metrics verification."


k8s-run-migration:
	kubectl -n bitcoin-bastion delete job bitcoin-bastion-migration --ignore-not-found
	kubectl -n bitcoin-bastion apply -f deploy/kubernetes/base/migration-job.yaml

k8s-run-postgres-migration-smoke:
	kubectl -n bitcoin-bastion delete job bitcoin-bastion-postgres-migration-smoke --ignore-not-found
	kubectl -n bitcoin-bastion apply -f deploy/kubernetes/base/postgres-migration-smoke-job.yaml

k8s-run-postgres-schema-parity:
	kubectl -n bitcoin-bastion delete job bitcoin-bastion-postgres-schema-parity --ignore-not-found
	kubectl -n bitcoin-bastion apply -f deploy/kubernetes/base/postgres-schema-parity-job.yaml

k8s-run-release-evidence:
	kubectl -n bitcoin-bastion delete job bitcoin-bastion-release-evidence --ignore-not-found
	kubectl -n bitcoin-bastion apply -f deploy/kubernetes/base/release-evidence-job.yaml

k8s-collect-evidence-artifacts:
	@echo "Collect artifacts via kubectl cp from completed job pods: release_evidence.json, postgres_migration_smoke.json, postgres_schema_parity.json"
