# Operations Runbook

This runbook defines operational response steps for Bitcoin Bastion runtime incidents.

## 1) Post-deploy verification

After each deploy:
1. Check service health: `GET /api/v1/health/live` and `GET /api/v1/health/ready`.
2. Check admin module status: `GET /api/v1/admin/status`.
3. Check recovery posture: `GET /api/v1/admin/jobs/recovery-check`.
4. Check observability snapshot: `GET /api/v1/observability/snapshot`.
5. Verify metrics endpoint: `GET /metrics`.

If any check fails, stop rollout and proceed to rollback section.

### Exact verification command set (record output in release evidence)
```bash
# API health
curl -fsS http://localhost:8000/api/v1/health/live
curl -fsS http://localhost:8000/api/v1/health/ready

# governance/admin
curl -fsS -H "Authorization: Bearer <ADMIN_TOKEN>" http://localhost:8000/api/v1/admin/status
curl -fsS -H "Authorization: Bearer <ADMIN_TOKEN>" http://localhost:8000/api/v1/admin/jobs/recovery-check
curl -fsS -H "Authorization: Bearer <ADMIN_TOKEN>" http://localhost:8000/api/v1/observability/snapshot

# runtime metrics
curl -fsS http://localhost:8000/metrics
```

## 2) Runtime governance interpretation

When reading `/api/v1/observability/snapshot`:
- `runtime_severity.level`: aggregate runtime posture (`ok|warning|critical`).
- `runtime_severity.escalation_required`: escalation gate for operator paging.
- `degraded_mode.active`: explicit degraded runtime mode flag.
- `degraded_mode.reasons`: degraded dependencies (e.g. stale chain/mempool, provider outage, delivery degradation).
- `operational_evidence`: compact audit packet for triage (runtime state, provider quality, unresolved findings, delivery/drill/recovery posture).

Governance rule: if `degraded_mode.active=true`, treat confidence-bearing outputs as reduced-confidence until recovery actions complete.

## 3) Failed background jobs

If `/api/v1/admin/jobs/recovery-check` reports `job_failure` issues:
1. Inspect `/api/v1/admin/jobs/runs` for task names and recent error payloads.
2. Retry safe task classes using `POST /api/v1/admin/jobs/retry`.
3. For repeated failures, disable recurring trigger and investigate provider/database dependencies.
4. Re-run recovery check and confirm failures are clearing.

## 4) Failed deliveries

If recovery check reports `delivery_failure` issues:
1. Verify destination/channel settings.
2. Re-run publish task (`delivery.publish`) once destination and rate-limit conditions are stable.
3. Confirm sent counters improve in `/api/v1/observability/snapshot`.
4. Track delivery failures over the next 24h for regression.

## 5) Degraded/fallback response workflow

Escalate promptly when one or more apply:
- `runtime_severity.level == "critical"`
- `runtime_severity.escalation_required == true`
- `degraded_mode.reasons` includes provider or observability outage markers
- `operational_evidence.unresolved_critical_findings > 0`

Actions:
1. Freeze high-impact policy automation and treasury-sensitive actions.
2. Recover provider freshness (probe/failover) and confirm fallback clears.
3. Run/queue highest-priority drill from `operational_evidence.drill_status`.
4. Reassess recovery SLO status and unresolved findings.
5. Document incident timeline and residual risk before resuming automation.

## 6) Rollback procedure

Rollback should be initiated when:
- Health checks fail after deploy and cannot be remediated quickly.
- Recovery check shows rapidly increasing failures.
- Policy/treasury critical endpoints return persistent 5xx.

Rollback steps:
1. Re-deploy previous known-good image.
2. Re-run migration compatibility check (`bash scripts/check_alembic_reproducibility.sh`).
3. Re-run post-deploy verification checklist.
4. Record incident summary and residual risks.

### Rollback checklist (operator copy/paste)
- [ ] Freeze high-impact automation (policy/treasury).
- [ ] Pin and deploy last known-good image digest.
- [ ] Validate DB migration compatibility path before traffic shift.
- [ ] Run health/governance verification commands.
- [ ] Confirm recovery-check severity is not worsening.
- [ ] Confirm metrics endpoint is scraping successfully.
- [ ] Document incident timeline, trigger, blast radius, and residual risk.

### Rollback verification commands
```bash
# 1) compatibility + parity checks
bash scripts/check_alembic_reproducibility.sh
python scripts/check_schema_runtime_parity.py

# 2) service verification after rollback deploy
curl -fsS http://localhost:8000/api/v1/health/live
curl -fsS http://localhost:8000/api/v1/health/ready
curl -fsS -H "Authorization: Bearer <ADMIN_TOKEN>" http://localhost:8000/api/v1/admin/jobs/recovery-check
curl -fsS http://localhost:8000/metrics
```

## 7) Governance-sensitive policy changes

For policy catalog changes with strict tightening:
1. Always include `change_justification` in policy catalog upsert payload.
2. Run policy simulation before activation (`POST /api/v1/policy/simulate`).
3. If simulation risk is high, require 2-person review and staged activation.

## 8) Evidence/recommendation traceability checks

For high-impact signals:
1. Inspect `/api/v1/signals/{signal_id}/recommendations` for `evidence_refs`, `evidence_paths`, and `policy_refs`.
2. Ensure actions and rationale are consistent with explainability graph artifacts.
3. Escalate to operator review for inconsistent or low-confidence traces.


## 9) Container deployment and reproducibility

### Required environment
1. Copy `.env.example` to `.env` and set non-default secrets (`POSTGRES_PASSWORD`, `JWT_SECRET_KEY`).
2. For production (`ENVIRONMENT=prod`), startup intentionally fails if `JWT_SECRET_KEY` is default/weak.

### Boot sequence
1. Build and start stack: `docker compose --env-file .env up -d --build`.
2. Verify dependencies are healthy: `docker compose ps`.
3. Verify app liveness: `GET /api/v1/health/live`.

### Migration path at deploy time
- API/worker/beat entrypoints run `alembic upgrade head` before starting process runtime.
- If migration fails, process exits non-zero and container restart policy handles retry/escalation.

### Service lifecycle expectations
- `db` and `redis` must report healthy before app/worker/beat startup proceeds.
- `worker` and `beat` depend on DB/Redis readiness and use deterministic startup scripts.

### Failure-safe behavior
- Missing required env vars (`DATABASE_URL`, `REDIS_URL`, `JWT_SECRET_KEY`) cause immediate startup failure.
- Production mode rejects insecure JWT secret values by design.

## 10) Incident response notes (release governance)
- Treat `runtime_severity.level == critical` as immediate incident response trigger.
- Treat unresolved critical findings in recovery SLO as release blocker until explicitly waived by operator + owner.
- For repeated job/delivery hotspot failures (>=3/24h), run focused drill before resuming automation.
- Any fallback-heavy runtime state during release must be captured as known limitation in release notes.


## 11) Post-release monitoring plan

### First 24 hours (high-frequency)

**Cadence:**
- Manual checks every 30 minutes for first 4 hours, then hourly to 24h.
- Automated telemetry is expected to update continuously, but operator review is still required.

**Checks:**
1. `/api/v1/observability/snapshot`
   - `runtime_severity.level`
   - `degraded_mode.active`
   - `operational_evidence.unresolved_critical_findings`
2. `/api/v1/admin/jobs/recovery-check`
   - `severity`
   - `failed_jobs_24h`
   - `failed_deliveries_24h`
3. `/metrics`
   - severity score / degraded mode gauges
   - provider share / delivery failure gauges
4. Health endpoints
   - `/api/v1/health/live`
   - `/api/v1/health/ready`

### First 7 days (stability window)

**Cadence:**
- Day 2–3: every 4 hours.
- Day 4–7: twice daily.
- Daily incident-review sync for open hotspots.

**Checks:**
- Trend failed jobs and deliveries across 24h windows.
- Confirm degraded mode does not persist without mitigation notes.
- Verify drill posture remains actionable (`next_drill_code`, `next_drill_priority`).
- Confirm protocol advisory outputs are not treated as consensus guarantees in operator actions.

### Critical monitoring domains

1. **Provider degradation monitoring**
   - Watch degraded reasons and provider freshness indicators in snapshot outputs.
   - Escalate if fallback/provider-outage markers persist beyond two consecutive review intervals.

2. **Telegram delivery monitoring**
   - Watch delivery failure hotspots and repeated destination failures.
   - Escalate if repeated delivery failures (>=3 in 24h for same destination) continue after retry-safe replay.

3. **Citadel scoring anomaly monitoring**
   - Watch abrupt score swings without corresponding evidence updates.
   - Treat unexplained severe downward score shifts as review-required before policy automation decisions.

4. **Chain-state/finality monitoring**
   - Track weak finality bands, stale provider freshness, and fallback data-source conditions.
   - Escalate if weak-finality/fallback posture persists across consecutive review windows.

### Manual vs automated responsibility

- **Automated (implemented):** telemetry emission, recovery-check computation, job/delivery counters, snapshot synthesis.
- **Manual (required):** interval reviews, incident classification, rollback decision, stakeholder communication, and release-risk sign-off.
- No fully autonomous rollback is assumed or claimed.
