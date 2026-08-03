.PHONY: install install-dev test test-contract test-integration test-unit plugin-test access-release-gate lint format up down up-prod run dev worker bot migrate alembic-repro alembic-roundtrip model-migration-coverage schema-runtime-parity db-schema-parity docs-truthfulness migration-smoke ci-smoke ci-release-gates compose-smoke postgres-migration-smoke postgres-schema-parity release-evidence k8s-render-staging k8s-render-production k8s-apply-staging k8s-apply-production k8s-status k8s-rollback-notes k8s-run-migration k8s-run-postgres-migration-smoke k8s-run-postgres-schema-parity k8s-run-release-evidence k8s-collect-evidence-artifacts k8s-render-gitops k8s-render-security k8s-render-observability k8s-render-autoscaling k8s-render-evidence k8s-render-rollout k8s-render-backup k8s-render-drills k8s-run-evidence-archive k8s-run-provider-failure-drill k8s-run-recovery-slo-drill k8s-backup-now k8s-restore-notes k8s-gitops-bootstrap-notes sbom vulnerability-scan provenance security-artifacts-notes k8s-render-runtime-security k8s-lockdown-notes k8s-burn-in-notes k8s-production-cutover-notes k8s-restore-validate-notes k8s-run-provider-outage-drill k8s-run-delivery-outage-drill k8s-operations-check k8s-operational-signoff-template k8s-render-observability-pack k8s-run-observability-validation k8s-alert-fatigue-notes k8s-incident-automation-notes runtime-render-kind runtime-render-minikube deploy-kind deploy-minikube runtime-profiles runtime-detect runtime-render-compose runtime-render-k8s runtime-render-k3s runtime-render-single-node deploy-compose deploy-k8s deploy-k3s deploy-single-node systemd-notes wallet-lnurl-auth-release-gate wallet-lnurl-auth-production-gate

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

plugin-test: install-dev
	python -m pytest -q tests/unit/test_plugin_manifest.py tests/unit/test_plugin_permissions.py tests/unit/test_plugin_registry.py tests/unit/test_plugin_sandbox.py tests/unit/test_plugin_loader.py tests/contract/test_plugin_api_safety.py

access-release-gate: install-dev
	python -m pytest -q tests/security/test_access_layer_release_gate.py
	python -m pytest -q tests/security/test_no_password_auth.py tests/security/test_no_bearer_access_pass.py tests/security/test_no_bitcoin_seed_auth.py tests/security/test_access_policy_required.py tests/security/test_access_replay_protection.py tests/security/test_access_revocation.py tests/security/test_access_sensitive_logging.py tests/security/test_access_recovery_abuse.py
	python -m pytest -q tests/contract/test_access_openapi_contract.py
	python -m pytest -q tests/integration/test_access_full_flow.py
	python -m pytest -q sdk/python/tests
	cd sdk/typescript && npm test

wallet-lnurl-auth-release-gate:
	bash scripts/wallet-lnurl-auth-release-gate.sh --candidate

wallet-lnurl-auth-production-gate:
	bash scripts/wallet-lnurl-auth-release-gate.sh --production

lint:
	python -m ruff check app cli tests
	python -m mypy app cli

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

ci-release-gates: install-dev access-release-gate
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


k8s-render-dev:
	kubectl kustomize deploy/kubernetes/overlays/dev

k8s-render-staging:
	kubectl kustomize deploy/kubernetes/overlays/staging

k8s-render-production:
	kubectl kustomize deploy/kubernetes/overlays/production

runtime-profiles:
	python deploy/scripts/render-runtime-profile.py --list

runtime-detect:
	python deploy/scripts/detect-runtime-profile.py

runtime-render-compose:
	python deploy/scripts/render-runtime-profile.py --profile compose --env local --dry-run

runtime-render-k8s:
	python deploy/scripts/render-runtime-profile.py --profile k8s --env production --dry-run

runtime-render-k3s:
	python deploy/scripts/render-runtime-profile.py --profile k3s --env production --dry-run

runtime-render-kind:
	python deploy/scripts/render-runtime-profile.py --profile kind --env local --dry-run

runtime-render-minikube:
	python deploy/scripts/render-runtime-profile.py --profile minikube --env local --dry-run

runtime-render-single-node:
	python deploy/scripts/render-runtime-profile.py --profile single-node --env production --dry-run

deploy-compose:
	python deploy/scripts/bastion-deploy apply --profile compose --env production --yes

deploy-k8s:
	python deploy/scripts/bastion-deploy apply --profile k8s --env production --yes

deploy-k3s:
	python deploy/scripts/bastion-deploy apply --profile k3s --env production --yes

deploy-kind:
	@echo "Kind deployment is for local Kubernetes validation/testing only; it is not production."
	python deploy/scripts/bastion-deploy apply --profile kind --env local --yes

deploy-minikube:
	@echo "Minikube deployment is for local operator testing only; it is not production."
	python deploy/scripts/bastion-deploy apply --profile minikube --env local --yes

deploy-single-node:
	@echo "Single-node deployment is constrained production-like/sovereign operation with no default HA."
	python deploy/scripts/bastion-deploy apply --profile single-node --env production --yes

systemd-notes:
	@cat docs/BARE_METAL_SYSTEMD.md

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

k8s-render-gitops:
	kubectl apply --dry-run=client -f deploy/kubernetes/gitops/

k8s-render-security:
	kubectl apply --dry-run=client -f deploy/kubernetes/security/

k8s-render-observability:
	kubectl apply --dry-run=client -f deploy/kubernetes/observability/prometheus-rules.yaml
	kubectl apply --dry-run=client -f deploy/kubernetes/observability/loki-values.example.yaml || true

k8s-render-autoscaling:
	kubectl apply --dry-run=client -f deploy/kubernetes/autoscaling/hpa-api.yaml

k8s-render-evidence:
	kubectl apply --dry-run=client -f deploy/kubernetes/evidence/

k8s-render-rollout:
	kubectl apply --dry-run=client -f deploy/kubernetes/rollout/

k8s-render-backup:
	kubectl apply --dry-run=client -f deploy/kubernetes/backup/

k8s-render-drills:
	kubectl apply --dry-run=client -f deploy/kubernetes/drills/

k8s-run-evidence-archive:
	kubectl -n bitcoin-bastion delete job bitcoin-bastion-evidence-archive --ignore-not-found
	kubectl -n bitcoin-bastion apply -f deploy/kubernetes/evidence/evidence-archive-job.yaml

k8s-run-provider-failure-drill:
	kubectl -n bitcoin-bastion delete job bitcoin-bastion-provider-failure-drill --ignore-not-found
	kubectl -n bitcoin-bastion apply -f deploy/kubernetes/drills/provider-failure-drill-job.yaml

k8s-run-recovery-slo-drill:
	kubectl -n bitcoin-bastion delete job bitcoin-bastion-recovery-slo-drill --ignore-not-found
	kubectl -n bitcoin-bastion apply -f deploy/kubernetes/drills/recovery-slo-drill-job.yaml

k8s-backup-now:
	kubectl -n bitcoin-bastion create job --from=cronjob/bitcoin-bastion-postgres-backup bitcoin-bastion-postgres-backup-now-$(shell date +%s)

k8s-restore-notes:
	@echo "Restore is manual-only. Set CONFIRM_RESTORE=YES_I_ACKNOWLEDGE_DATA_RISK and RESTORE_FILE, then apply postgres-restore-job.example.yaml intentionally."

k8s-gitops-bootstrap-notes:
	@echo "Bootstrap Argo CD apps from deploy/kubernetes/gitops. Promote via Git commits, collect staging evidence before production sync, rollback via git revert."

sbom:
	@mkdir -p artifacts
	@echo "Use CI workflow container-security.yml for canonical SBOM output at artifacts/sbom.spdx.json"

vulnerability-scan:
	@mkdir -p artifacts
	@echo "Use CI workflow container-security.yml for canonical vulnerability output at artifacts/vulnerability_report.json"

provenance:
	@mkdir -p artifacts
	@echo "Use CI workflow container-security.yml for canonical provenance output at artifacts/provenance.json"

security-artifacts-notes:
	@echo "Required security artifacts: sbom.spdx.json, vulnerability_report.json, provenance.json"

k8s-render-runtime-security:
	kubectl apply --dry-run=client -f deploy/kubernetes/security/

k8s-lockdown-notes:
	@echo "Emergency lockdown: apply deploy/kubernetes/security/emergency-lockdown-networkpolicy.yaml, verify blast radius, then revert after containment."

k8s-burn-in-notes:
	@cat deploy/kubernetes/operations/burn-in-checklist.md

k8s-production-cutover-notes:
	@cat deploy/kubernetes/operations/production-cutover-checklist.md

k8s-restore-validate-notes:
	@cat deploy/kubernetes/operations/backup-restore-validation.md

k8s-run-provider-outage-drill:
	kubectl -n bitcoin-bastion delete job bitcoin-bastion-provider-outage-drill --ignore-not-found
	kubectl -n bitcoin-bastion apply -f deploy/kubernetes/drills/provider-outage-drill-job.yaml

k8s-run-delivery-outage-drill:
	kubectl -n bitcoin-bastion delete job bitcoin-bastion-delivery-outage-drill --ignore-not-found
	kubectl -n bitcoin-bastion apply -f deploy/kubernetes/drills/delivery-outage-drill-job.yaml

k8s-operations-check:
	@echo "Operations docs present:"
	@test -f docs/KUBERNETES_PRODUCTION_OPERATIONS.md
	@test -f deploy/kubernetes/operations/burn-in-checklist.md
	@test -f deploy/kubernetes/operations/production-cutover-checklist.md

k8s-operational-signoff-template:
	@cat deploy/kubernetes/operations/operational-signoff-template.md


k8s-render-observability-pack:
	kubectl apply --dry-run=client -f deploy/kubernetes/observability/prometheus-rules-slo.yaml
	kubectl apply --dry-run=client -f deploy/kubernetes/observability/prometheus-rules-runtime.yaml
	kubectl apply --dry-run=client -f deploy/kubernetes/observability/prometheus-rules-provider-health.yaml
	kubectl apply --dry-run=client -f deploy/kubernetes/observability/prometheus-rules-citadel.yaml
	kubectl apply --dry-run=client -f deploy/kubernetes/observability/prometheus-rules-workers.yaml
	kubectl apply --dry-run=client -f deploy/kubernetes/observability/prometheus-rules-evidence-jobs.yaml

k8s-run-observability-validation:
	kubectl -n bitcoin-bastion delete job bitcoin-bastion-observability-validation --ignore-not-found
	kubectl -n bitcoin-bastion apply -f deploy/kubernetes/observability/observability-validation-job.yaml

k8s-alert-fatigue-notes:
	@cat deploy/kubernetes/observability/alert-fatigue-control.md

k8s-incident-automation-notes:
	@cat deploy/kubernetes/observability/incident-automation-notes.md


k8s-render-gitops-governance:
	kubectl apply --dry-run=client -f deploy/kubernetes/gitops/

k8s-gitops-approval-template:
	@cat deploy/kubernetes/gitops/production-approval-template.md

k8s-gitops-evidence-gate:
	@cat deploy/kubernetes/gitops/evidence-gate-checklist.md

k8s-gitops-drift-check-notes:
	@cat deploy/kubernetes/gitops/environment-drift-check-job.yaml


k8s-final-cert-notes:
	@cat docs/KUBERNETES_RC_CERTIFICATION.md

k8s-operator-runbook-lock:
	@cat docs/KUBERNETES_OPERATOR_RUNBOOK_LOCK.md

k8s-readiness-matrix:
	@cat docs/FINAL_KUBERNETES_READINESS_MATRIX.md

sdk-python-install:
	cd sdk/python && python -m pip install -e '.[dev]'

sdk-python-lint:
	cd sdk/python && python -m ruff check bitcoin_bastion_sdk tests
	cd sdk/python && python -m mypy bitcoin_bastion_sdk

sdk-python-test:
	cd sdk/python && python -m pytest -q

sdk-python-check: sdk-python-lint sdk-python-test

cli-help:
	python -m cli.bastion_cli.main --help

cli-health:
	bastion health

cli-smoke:
	bastion health
	bastion status

mcp-install:
	cd mcp && python -m pip install -e '.[dev]'

mcp-test:
	cd mcp && python -m pytest -q

mcp-lint:
	cd mcp && python -m ruff check bastion_mcp

mcp-typecheck:
	cd mcp && python -m mypy bastion_mcp

mcp-run:
	cd mcp && python -m bastion_mcp.server

ts-sdk-install:
	cd sdk/typescript && npm install

ts-sdk-build:
	cd sdk/typescript && npm run build

ts-sdk-typecheck:
	cd sdk/typescript && npm run typecheck

ts-sdk-test:
	cd sdk/typescript && npm test

ts-sdk-check: ts-sdk-typecheck ts-sdk-test

.PHONY: reflex-docker-build reflex-docker-run compose-reflex compose-reflex-down compose-full-reflex compose-full-reflex-down runtime-render-reflex

reflex-docker-build:
	docker build -f frontend/Dockerfile -t bitcoin-bastion-reflex-frontend:local frontend

reflex-docker-run:
	docker run --rm -p 3001:3001 -p 8001:8001 -e BB_API_BASE_URL=$${BB_API_BASE_URL:-http://host.docker.internal:8000} bitcoin-bastion-reflex-frontend:local

compose-reflex:
	docker compose -f deploy/compose/reflex-frontend.compose.yaml up -d --build

compose-reflex-down:
	docker compose -f deploy/compose/reflex-frontend.compose.yaml down

compose-full-reflex:
	docker compose -f deploy/compose/full-reflex.compose.yaml up -d --build

compose-full-reflex-down:
	docker compose -f deploy/compose/full-reflex.compose.yaml down

runtime-render-reflex:
	docker compose -f deploy/compose/full-reflex.compose.yaml config >/dev/null
	python deploy/scripts/render-runtime-profile.py --profile compose --env local --dry-run

.PHONY: reflex-sync reflex-lint reflex-typecheck reflex-test reflex-export reflex-ci frontend-safety-check frontend-route-parity

reflex-sync:
	cd frontend && uv sync

reflex-lint:
	cd frontend && uv run ruff check .

reflex-typecheck:
	cd frontend && uv run mypy bastion_ui

reflex-test:
	cd frontend && uv run pytest

reflex-export:
	cd frontend && uv run reflex export

frontend-safety-check:
	cd frontend && uv run pytest bastion_ui/tests/test_forbidden_wording.py bastion_ui/tests/test_no_sensitive_input.py bastion_ui/tests/test_trace_safety.py bastion_ui/tests/test_market_no_trading_claims.py bastion_ui/tests/test_console_safety.py bastion_ui/tests/test_public_forbidden_wording.py

frontend-route-parity:
	cd frontend && uv run pytest bastion_ui/tests/test_routes.py bastion_ui/tests/test_navigation.py bastion_ui/tests/test_command_palette.py bastion_ui/tests/test_market_routes.py bastion_ui/tests/test_console_routes.py bastion_ui/tests/test_console_advanced_routes.py

reflex-ci: reflex-sync reflex-lint reflex-typecheck reflex-test reflex-export frontend-safety-check frontend-route-parity

.PHONY: frontend-reflex-check frontend-reflex-export frontend-parity-check frontend-primary-switch-check

frontend-reflex-check: reflex-sync reflex-lint reflex-typecheck reflex-test

frontend-reflex-export: reflex-export


frontend-parity-check: frontend-safety-check frontend-route-parity

frontend-primary-switch-check: frontend-reflex-check frontend-reflex-export frontend-parity-check
	@echo "Frontend primary switch check passed for Reflex-specific gates; see docs/FRONTEND_PRIMARY_SWITCH.md for delegated Market and known root-suite blockers."
