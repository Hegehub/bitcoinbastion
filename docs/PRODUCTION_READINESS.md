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
