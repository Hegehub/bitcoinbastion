# Production Readiness Checklist

This checklist is release-time evidence capture. Items must be verified per release.

## Label meanings
- **IMPLEMENTED**: capability exists in repository.
- **BASELINE**: capability exists but requires deeper operational validation.
- **SYNTHETIC**: placeholder behavior exists and must not be treated as production-grade.

## Release-candidate (RC) exit criteria
All criteria below must be met before promoting an RC to production:
- [ ] `make lint` passes.
- [ ] `python -m pytest -q tests/unit` passes.
- [ ] `python -m pytest -q tests/integration` passes.
- [ ] `python -m pytest -q tests/contract` passes.
- [ ] `python -m pytest -q tests/regression` passes.
- [ ] `make ci-release-gates` passes (migration replay + parity + docs truthfulness).
- [ ] Post-deploy verification commands (health, admin status, recovery check, observability snapshot, metrics) are captured with timestamps.
- [ ] Known BASELINE/SYNTHETIC limitations acknowledged in release sign-off.

## Final P6-10 decision guard
- Current repository-level sovereignty-grade readiness: **89%** (see `docs/STATUS.md`).
- **Do not claim 100% readiness** until all residual risks in `docs/STATUS.md` are explicitly closed with deployment evidence.
- RC promotion is currently **RC-ready pending environment evidence**; do not declare full production deployment readiness until evidence artifacts are attached.

## Runtime and infrastructure
- [ ] Docker image build reproduced for release commit.
- [ ] Compose/runtime topology validated for API, DB, Redis, worker, beat.
- [ ] Health/readiness probes validated in target environment.
- [ ] Migration step executed and logged for deployment.
- [ ] Compose stack boot verified with health checks (`docker compose up -d --build` + service health status).
- [ ] Startup fails safely when required env/secrets are missing or insecure in production mode.
- [ ] Worker/beat startup ordering confirms Redis/Postgres readiness dependencies.

## Security and access
- [ ] Secrets sourced from environment/secret manager.
- [ ] JWT/admin guard behavior verified in staging.
- [ ] Audit-log generation verified for privileged actions.
- [ ] No-custody posture verified (no seed phrase/private-key handling paths in API/runtime).
- [ ] Admin RBAC guard verified for sensitive policy/treasury/admin endpoints (no silent bypass).

## Data and migrations
- [ ] Alembic head and migration chain verified on release commit.
- [ ] Migration reproducibility smoke passes (`make migration-smoke`).
- [ ] Schema parity checks pass (`python scripts/check_schema_runtime_parity.py`).
- [ ] Backward compatibility review completed for schema and API changes.
- [ ] Migration replay verified (`alembic upgrade head -> downgrade base -> upgrade head`) on a clean database artifact.
- [ ] Column/nullability/default/index/constraint parity checks reviewed (`python scripts/check_schema_runtime_parity.py`) and accepted drift (if any) documented.
- [ ] Rollback notes prepared for release migration set (expected downgrade path, data-loss caveats, operator decision points).
- [ ] Dialect-specific limitations acknowledged (SQLite parity is deterministic CI baseline; PostgreSQL semantics must be validated in staging for final sign-off).

## Reliability and observability
- [ ] Verify protocol source-quality labels are present for on-chain/citadel outputs (provider vs fallback vs mock).
- [ ] Verify fallback/synthetic protocol domains lower decision confidence in operational runbooks.
- [ ] Verify observability snapshot includes runtime severity, degraded mode, and operational evidence packet.
- [ ] Verify runtime metrics are exposed at `/metrics` for: severity score, degraded mode active, provider share, delivery failures, unresolved findings, citadel runtime health.
- [ ] Retry/timeout behavior verified for external integrations.
- [ ] Background job idempotency checks reviewed for touched tasks.
- [ ] Request IDs, logs, and metrics validated in deployed environment.
- [ ] Job execution telemetry available for operational triage.

## Recovery, drill, and SLO governance
- [ ] Recovery SLO status and unresolved critical findings are visible in `/api/v1/admin/jobs/recovery-check` and `/api/v1/observability/snapshot`.
- [ ] Drill posture (`next_drill_code`, `next_drill_priority`, `automated_drills_ready`) is reviewed weekly.
- [ ] Escalation thresholds are validated against environment-specific paging policies to reduce alert fatigue.
- [ ] Degraded mode and fallback semantics are acknowledged in release sign-off when active.

## Truth constraints
- Do not infer production SLO attainment from implemented endpoints.
- Treat **SYNTHETIC** and **BASELINE** components as non-final until explicitly hardened.
- Avoid percentage readiness claims in release documentation.

## Known limitations (must be visible in every release sign-off)
- **BASELINE**: Telegram/delivery reliability is environment-dependent and requires deployment-specific validation.
- **BASELINE**: Mempool/UTXO/script analyzers are advisory and deterministic over provided snapshots/hints.
- **SYNTHETIC**: Parts of Citadel disaster and dependency simulation remain deterministic synthetic models.
- **Constraint**: Runtime confidence/finality values are operational heuristics, not consensus proofs.

## Protocol maturity caveats
- Chain-state confidence is operational and conservative; it is not a consensus finality proof.
- Mempool/UTXO/script analytics are snapshot/hint-driven and must be treated as advisory unless corroborated by provider-grade evidence.


## Security verification commands (P7-02)
```bash
rg -n "seed phrase|seed_phrase|mnemonic|private key|private_key|xprv|xpriv|wif|BEGIN PRIVATE KEY" app tests
rg -n "Depends\(get_admin_user\)" app/api/v1
python -m pytest -q tests/unit/test_config_guards.py tests/unit/test_auth_dependencies.py tests/integration/test_treasury_admin_guards.py tests/integration/test_error_envelope.py tests/unit/test_treasury_approval_runtime.py tests/unit/test_policy_runtime_service.py
python -m pytest -q tests/unit/test_auth_service.py tests/unit/test_audit_repository.py tests/unit/test_signal_publish_service.py
```


## Documentation verification commands (P7-03)
```bash
python scripts/check_docs_truthfulness.py
python -m pytest -q tests/contract/test_runtime_api_contracts.py tests/integration/test_error_envelope.py
```


## Release metadata checklist (P7-04)
- [ ] Version candidate label recorded in release notes (example: `v0.1.0-rc.1`).
- [ ] Upgrade notes recorded (JWT/env requirements, migration before traffic).
- [ ] Migration notes recorded (replay/parity outcomes and dialect caveat).
- [ ] Known limitations copied from `docs/STATUS.md` into release notes.
- [ ] Rollback notes completed with prior digest/version and verification evidence.


## Post-release incident severity matrix (P7-05)

| Severity | Trigger examples | Required response |
|---|---|---|
| Sev-0 (Critical) | Runtime severity critical with unresolved critical findings; sustained health/readiness failures; repeated policy/treasury 5xx | Immediate incident command, freeze high-impact automation, evaluate rollback now |
| Sev-1 (High) | Degraded mode active with escalating failed jobs/deliveries; persistent provider outage/fallback conditions | Mitigate within same shift, run focused drill/replay, prepare rollback decision packet |
| Sev-2 (Medium) | Intermittent delivery/provider degradation without hard outage; isolated anomaly requiring human review | Track and remediate in-day, increase monitoring cadence, document residual risk |
| Sev-3 (Low) | Non-impacting noise, transient warnings resolved quickly | Record in ops log, continue standard cadence |

### Rollback triggers (explicit)
- Sev-0 condition persisting across two consecutive review intervals.
- Health/readiness checks repeatedly failing after immediate remediation attempts.
- Recovery-check trend indicates accelerating critical hotspots despite replay of safe tasks.
- Policy/treasury critical paths exhibit persistent operational errors that block safe governance actions.


## P7-06 final decision gate
- Current final decision: **PRE-RC / PRODUCTION-ORIENTED BETA**.
- Promotion to `PRODUCTION RELEASE CANDIDATE` requires explicit closure evidence for:
  1. protocol maturity realism in operational workflows,
  2. Citadel synthetic-risk reduction or formal acceptance,
  3. full target-environment operations/deployment evidence capture.


- Provider health pipeline now executes real on-chain probes (with fallback/error sanitization), plus RSS/delivery evidence snapshots and bounded provider-health metrics labels.

- Observability snapshot now includes provider stale-evidence flags, fallback/mock/degradation reasons, provider confidence, and operator guidance; metrics now include provider status, latency, fallback active, confidence, last-success age, and failure counts with bounded labels.


- [ ] PostgreSQL staging validation executed and archived (`docs/POSTGRES_VALIDATION.md`).
- [ ] Release evidence pack generated and attached (`docs/DEPLOYMENT_EVIDENCE_PACK.md`).
  - Required artifacts: `artifacts/release_evidence.json`, `artifacts/postgres_migration_smoke.json`, `artifacts/postgres_schema_parity.json`.

- [ ] Citadel synthetic risk register reviewed and acknowledged (`docs/CITADEL_SYNTHETIC_RISK_REGISTER.md`).


## Final RC audit record
- Decision: **RC-ready pending environment evidence** (2026-05-18).
- Blocking gate: target-environment evidence artifacts not yet attached.
- See: `docs/FINAL_PRODUCTION_GAP_AUDIT.md`.

## Kubernetes target-environment foundation (P7-K8S)
- [ ] Kubernetes manifests rendered successfully (`make k8s-render-staging`, `make k8s-render-production`).
- [ ] Kubernetes deployment evidence captured from target environment (`make k8s-status` output + health/readiness/metrics curls).
- [ ] Secrets are provisioned from secret manager (no plaintext production credentials in git).
- [ ] NetworkPolicy enforcement validated for API ingress, Prometheus metrics scrape, and Redis/PostgreSQL egress.
- [ ] ServiceMonitor scrape verified in monitoring stack.
- [ ] Rollback runbook includes overlay/image pin strategy (`make k8s-rollback-notes`).

Kubernetes manifests improve deployment consistency but **do not alone satisfy RC promotion**. RC status remains tied to real environment evidence artifacts.

### Kubernetes RC blocker closure evidence
- [ ] `migration-job` executed successfully in target namespace.
- [ ] `postgres-migration-smoke-job` executed and artifact captured.
- [ ] `postgres-schema-parity-job` executed and artifact captured.
- [ ] `release-evidence-job` executed and artifact captured.
- [ ] All three blocker artifacts attached to release decision packet.

### Sovereign Kubernetes runtime layer (P7-K8S-SOVEREIGN)
- [ ] GitOps staging->production promotion flow is enforced and documented.
- [ ] Production deployment changes happen through GitOps (manual kubectl only for emergency break-glass).
- [ ] External Secrets integration configured for selected secret backend.
- [ ] Kyverno guardrails active (audit/enforce per rollout plan).
- [ ] Prometheus rules + Alertmanager routing validated in target environment.
- [ ] Grafana runtime dashboard imported and verified.
- [ ] Evidence archive job executed with checksum output.
- [ ] Backup CronJob executed and restore drill performed in staging.
- [ ] Provider/recovery/disaster drills executed and attached to release evidence.

- [ ] Dedicated namespaces exist: `bitcoin-bastion-staging` and `bitcoin-bastion-prod`.

- [ ] Supply-chain artifacts attached (SBOM, vulnerability report, provenance).
- [ ] Production overlay images pinned to approved immutable digests.
- [ ] Signed-image verification policy enabled (Audit/Enforce per rollout stage).

- [ ] Runtime security checklist completed (`docs/KUBERNETES_RUNTIME_SECURITY.md`).
- [ ] RBAC least-privilege service accounts bound and default SA unused.
- [ ] Emergency lockdown NetworkPolicy validated in staging.

- [ ] Production burn-in checklist completed and archived.
- [ ] Production cutover checklist completed before traffic shift.
- [ ] Operational sign-off template completed and attached.
- [ ] Backup verification evidence attached pre-cutover.
- [ ] Provider and delivery outage drills executed and evidence attached.
- [ ] Internal SLO baseline accepted as operational target (not public SLA).

- [ ] Observability validation job passed in target environment.
- [ ] SLO/rule packs reviewed and alert routing tested.
- [ ] Alert fatigue controls acknowledged and tuned per environment.

- [ ] GitOps promotion gates satisfied for current release.
- [ ] Production approval template completed and attached.
- [ ] Drift check run and no unapproved production drift present.

## Final Kubernetes RC certification lock
- [ ] `docs/KUBERNETES_RC_CERTIFICATION.md` reviewed.
- [ ] `docs/FINAL_KUBERNETES_READINESS_MATRIX.md` reviewed.
- [ ] `docs/KUBERNETES_OPERATOR_RUNBOOK_LOCK.md` accepted by operators.
