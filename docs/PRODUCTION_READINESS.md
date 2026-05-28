# Production Readiness

## Bastion Trace readiness

Implemented now:
- Backend baseline route/service/model coverage for core trace + tiers + integrations + observability.

Baseline/placeholder now:
- Deterministic weighting/scoring and non-calibrated provider quality semantics.
- Business/enterprise controls that depend on external auth/SSO/SIEM/policy enforcement.

Required before production-complete claim:
- Production calibration evidence for scoring/source weights.
- Production-validated external source adapters.
- Full graph intelligence hardening.
- Public Lite endpoint rate-limiting evidence.
- Production Telegram runtime/token evidence (if used).
- Auth/rate-limit enforcement evidence for business/enterprise endpoints.
- UI implementation and operational rollout evidence.

Explicit open gaps:
- No production calibration of scoring weights.
- No production external source adapters validated.
- No full graph intelligence.
- No ML.
- No frontend website UI yet.
- No production rate limiting evidence for public Lite endpoint.
- No production Telegram token/runtime evidence unless configured.
- Business/Enterprise enforcement depends on auth/policy infrastructure.
- Enterprise RBAC/SSO/SIEM are placeholders unless configured.
- Proof packets are unsigned unless signing exists.


## Public website backend gaps
- No frontend UI yet
- Public APIs require production auth/rate limiting review
- Public APIs require deployment hardening
- No CDN/WAF evidence yet
- No production observability validation yet
- No production calibration evidence yet
- Frontend contracts may evolve


## Frontend production gaps
- Frontend security review pending
- CSP/WAF/CDN hardening pending
- Production accessibility audit pending
- Production mobile QA pending
- Frontend E2E tests incomplete
- Backend/frontend contract stabilization pending
- No production deployment evidence yet


Production frontend hardening is still pending.

- Public endpoint rate limiting validation pending
- Frontend production security review pending
- No production UX telemetry validation yet
- No production accessibility audit yet
- Advanced Trace visualizations not implemented
- No production calibration evidence yet

Advanced graph visualization not implemented
Production accessibility audit pending
Frontend E2E coverage incomplete
Timeline performance validation pending
Proof packet signing/certification not implemented
No production calibration evidence yet

Business UI requires auth/rate-limit review
Review Desk requires production user/role model
Enterprise RBAC/SSO are placeholders unless configured
SIEM delivery requires deployment configuration
Audit immutability is application-level unless WORM/DB controls exist
Legal Hold is operational metadata and not legal advice
Frontend E2E tests still incomplete

Operations dashboard is informational only
No infrastructure mutation/control plane implemented
Production deployment evidence incomplete
Staging validation incomplete
No production calibration evidence
Runtime event scaling not validated
Frontend E2E coverage incomplete

Production accessibility audit pending or partially complete
Production security review pending or partially complete
E2E coverage baseline unless full suite exists
CDN/CSP/WAF configuration pending
Production telemetry/privacy review pending
Backend calibration still pending
Deployment evidence still pending

API contracts baseline locked, not final external SLA
OpenAPI should be reviewed before public API launch
Automated TypeScript generation may be pending
Auth/rate limiting still required for production public exposure
Contract tests cover critical paths but not every future endpoint

Penetration testing pending
WAF/CDN deployment pending
Infrastructure-level rate limiting pending
Production TLS validation pending
Production CSP tuning pending
Full security review pending
Third-party dependency audit pending

Production cluster validation pending
Load testing pending
Production observability tuning pending
Disaster recovery drills pending
Penetration testing pending
Secrets-management integration pending
Production autoscaling validation pending

No real production calibration evidence
No production load testing evidence
No real disaster recovery validation
No production runtime metrics validation
No penetration testing completion evidence
No production deployment evidence yet

Real staging validation pending
Production deployment evidence pending
Production load testing pending
Penetration testing pending
Accessibility certification pending
Full operational drills pending
Production calibration pending

Production calibration incomplete
No production load-testing evidence
No penetration testing completion evidence
No production deployment evidence
No real disaster recovery drill evidence
No accessibility certification
No production operational metrics baseline

## Market Data Engine
- BTC provider aggregation, confidence, degraded mode, and replayability evidence fields implemented in foundation form.

## BTC Candle Engine
- Production candle storage and deterministic rebuild baseline implemented.

- Market candle build runs and provider snapshots baseline implemented.

- Intelligence timeline foundation added with replay-safe hashing and deterministic ordering baseline.

- Market health snapshot endpoint and BTC price history contract aligned for operator visibility.

- News scoring now emits explainable factors + limitations and avoids mandatory AI dependencies.

- News price impact engine now exposes confidence breakdown, impact bands, delayed reaction and false-signal flags.

## News Impact Engine readiness

The News Impact Engine records degraded price/provider state instead of hiding missing data. It persists confidence inputs, window snapshots, and limitations for operator audit. Outputs remain correlation-based and are not financial advice.

## Candle Attribution Production Readiness

Candle attribution remains operator-reviewable and correlation-oriented. The engine records confidence bands, score contributions, provider health, degraded-state limitations, and replay snapshots so operators can audit why an event was ranked near a candle. It does not generate trading signals or claim causation.
