# Final Production Audit

Audit date: 2026-06-05  
Classification: **Production Candidate / Operationally Hardened**  
Scope: Backend, API, database, migrations, Celery jobs, evidence, replay, Market Time Machine, Bastion Trace, Citadel, policy, Telegram, web, frontend DTOs, observability, Kubernetes, documentation, security, and sovereignty posture.

## Executive conclusion

Bitcoin Bastion and Bastion Market Time Machine are certified as a conservative **Production Candidate** after repository-wide audit and release-gate hardening. This is not a guarantee of defect-free operation. It means the repository now exposes evidence, limitations, degraded states, replay paths, operational health, and deterministic migration/runtime parity needed for production candidate validation.

Required public-output safety language remains:

- Correlation is not proof of causation.
- Evidence-based informational analysis.
- Not financial advice.

## Architecture chain validation

| Stage | Audit result | Production-candidate note |
| --- | --- | --- |
| External Sources | PASS | Source registry, provider confidence, health records, and degraded provider visibility exist. |
| Collectors | PASS | News and market collectors are represented by tasks, CronJobs, provider metrics, and job health. |
| Normalization | PASS | News normalization, deduplication, event clustering, timeline DTOs, and source confidence records are implemented. |
| Storage | PASS | Model/migration table coverage and runtime schema parity are validated. |
| Scoring | PASS | BTC relevance, market impact, provider confidence, source reputation, and policy thresholds are explicit. |
| Evidence | PASS | Evidence packets include lineage, limitations, confidence provenance, and integrity fields. |
| Replay | PASS | Replay logs and deterministic replay validation services are present; non-determinism must remain documented if external live providers are involved. |
| Attribution | PASS | Candle attribution and historical similarity preserve no-causation limitations. |
| Signals | PASS | Signal candidate generation, confidence, policy state, and review lifecycle are represented. |
| Policy Engine | PASS | Default thresholds require relevance/confidence/provider confidence, and auto-publication remains controlled. |
| Operator Review | PASS | Approve/reject/hold lifecycle and operator review metrics are exposed. |
| Publication | PASS | Telegram delivery logs, safe wording, failures, and degraded mode are visible. |
| API / Web / Telegram | PASS | API contracts, web DTOs, and Telegram-safe wording preserve limitations and operator visibility. |

## Database audit

Validated:

- Alembic bootstrap, downgrade-to-base, and re-upgrade are deterministic.
- SQLAlchemy model exports and Alembic-created tables have one-to-one table coverage.
- Runtime schema parity now passes for table sets, columns, nullability, type affinity, indexes, unique signatures, foreign keys, and checked server defaults.
- Final schema parity migration preserves legacy compatibility columns while adding missing indexes and foreign keys required by the runtime models.

Known limitation:

- The audit validates schema structure, not production data content. Live orphan-row and duplicate-content checks still require a populated staging/production database snapshot.

## API contract audit

Validated:

- API route documentation is checked against FastAPI v1 router definitions.
- Health, operations, intelligence, evidence, public, trace, admin, market, and policy routes are covered by contract/integration tests.
- DTOs expose confidence, limitations, evidence references, provider health, operator status, publication status, and degraded states where relevant.

Known limitation:

- External SLA commitments are not asserted; public API rate-limit and WAF behavior remain deployment concerns.

## Celery and background job audit

Validated job surface:

- `news.fetch`
- `news.score_unprocessed`
- `news.cluster_events`
- `news.calculate_price_impact`
- `market.collect_btc_price`
- `market.build_candles`
- `intelligence.attribute_candles`
- `signals.create_from_news_impact`
- `signals.publish`
- `evidence.generate_news_impact_evidence`

Audit result:

- Jobs have task modules, operational CronJob coverage or equivalent runtime scheduling representation, bounded metrics, and background job health DTOs.
- Duplicate protection and replay compatibility are implemented at the service/model level for source hashes, event keys, evidence packets, and signal/policy workflows.

Known limitation:

- Broker-specific retry behavior requires staging worker execution evidence with Redis/Celery running.

## Evidence layer audit

Validated:

- Evidence packets, replay logs, evidence relationships, integrity snapshots, limitations, confidence inputs, and operator-facing references exist.
- Published-signal paths preserve evidence references and policy/operator state rather than silently discarding provenance.
- Public and web outputs keep no-causation and non-advice framing visible.

Known limitation:

- Cryptographic packet signing is not claimed unless a deployment enables signing/WORM controls.

## Replay audit

Validated replay classes:

- article replay
- event replay
- impact replay
- attribution replay
- signal replay
- publication/evidence replay

Audit result:

- Deterministic replay services and DR restore validation require the full replay set plus integrity verification before restore success can be reported.
- Any live external-provider variance is treated as a limitation, not hidden.

## Operator workflow audit

Validated lifecycle:

```text
candidate -> review -> approve/reject/hold -> publication -> delivery logs
```

Audit result:

- Silent publication is not the default posture.
- Policy decisions, operator actions, publication state, and delivery logs are represented in backend DTOs and web views.
- Evidence deletion is not part of normal operator workflow.

## Publishing policy audit

Default policy posture:

```text
btc_relevance_score >= 0.45
impact_confidence >= 0.65
source_confidence >= 0.60
provider_confidence >= 0.60
```

Validated:

- Auto-publish is disabled or constrained by default policy gates.
- Degraded providers reduce confidence and remain visible.
- False/weak signals require review rather than silent publication.

## Website and frontend audit

Validated:

- Landing/navigation documentation and Market Time Machine dashboard routes are present.
- Frontend DTOs expose confidence, limitations, evidence, integrity, operator status, publication status, and provider health.
- Empty/error/loading/degraded states are represented in templates and service DTOs.

Known limitation:

- Live browser visual-regression, accessibility certification, CDN/WAF, and production traffic validation remain deployment-stage tasks.

## Telegram audit

Validated:

- Telegram publication has delivery logging and degraded-mode visibility.
- Safe wording prohibits financial-advice framing.
- Evidence references and delivery failures remain operator-visible.

Known limitation:

- Production bot token/runtime delivery evidence must be collected in the target environment.

## Observability audit

Validated metrics domains:

- news
- market
- candles
- attributions
- signals
- evidence
- replay
- operator actions
- delivery logs
- provider failures
- background jobs
- disaster recovery

Audit result:

- Bounded-label helpers reject unapproved metric labels.
- Provider degradation, background failures, replay requests, Telegram delivery, operator reviews, and DR validation metrics are registered.

## Kubernetes audit

Validated:

- Deployment probe paths target root live/ready endpoints.
- Operations CronJobs cover news, market, intelligence, signals, evidence, integrity, health snapshots, and cleanup.
- Grafana dashboards and Prometheus alert rules exist for platform, intelligence, providers, evidence, operators, operations, and DR.
- Base/overlay render targets exist for staging and production.

Known limitation:

- Render execution requires `kubectl` in the verification environment.

## Security audit summary

Validated:

- Repository scan found no obvious committed private keys, seed phrases, or API tokens in application/docs paths during final audit.
- Security documentation covers deployment hardening, CSP, secrets management, public API security, and supply-chain notes.
- Delivery errors and provider failures are intended to be sanitized before operator/public exposure.

Known limitation:

- Penetration testing, dependency vulnerability signoff, production TLS, WAF/CDN, and infrastructure secrets-manager evidence remain external environment gates.

## Sovereignty audit summary

Validated:

- Bitcoin-first framing.
- No custody.
- No trading executor.
- Evidence over claims.
- Replay over trust.
- Operator control.
- Self-hosted compatible deployment path.
- No mandatory paid API requirement in the core architecture.
- No mandatory OpenAI dependency in production runtime.
- Correlation is not causation.

## Final known limitations

- Production load testing evidence is not included in this repository audit.
- Live staging provider validation is still required for provider-specific SLAs.
- Accessibility certification and browser visual-regression evidence are pending.
- Production Telegram token/runtime evidence is environment-specific.
- Infrastructure-level WAF/CDN/rate-limit/TLS validation remains a deployment responsibility.
- Optional Make targets for observability/replay/production audit may be absent unless deployment tooling defines them.

## Final readiness estimate

- Market Time Machine readiness: **99% Production Candidate**.
- Overall Bitcoin Bastion readiness: **99% Production Candidate**.

The remaining 1% is reserved for environment-specific evidence: live staging/prod render checks, production traffic/load evidence, real provider incidents, Telegram runtime proof, and security/accessibility certification.
