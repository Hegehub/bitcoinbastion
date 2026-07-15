# Production Readiness

Lifecycle: **ACTIVE**

Last verified: **2026-07-15**

Current decision: **NOT PRODUCTION-READY**

This document defines release evidence and decision criteria. Current component
status belongs in [STATUS.md](STATUS.md); historical release reports belong in
`docs/archive/audits/`.

## Decision rule

Production readiness is binary for a named revision and target environment. It
requires all mandatory repository gates plus environment-specific operational
evidence. The existence of code, manifests, tests, or evidence generators is
not proof that an environment passed.

Do not publish percentage readiness estimates.

## Mandatory repository gates

| Gate | Required evidence | Current state |
| --- | --- | --- |
| Code quality | Ruff and MyPy pass with the repository's declared scope. | FAIL |
| Unit and integration tests | Required suites pass without weakening security expectations. | FAIL |
| Contract tests | API, SDK, event, and frontend contracts pass. | PARTIAL |
| Proof-of-Access | Focused access gate and protected-route integration pass. | FOCUSED PASS / INTEGRATION FAIL |
| Migration replay | Clean bootstrap and supported upgrade/replay paths pass. | PARTIAL |
| Schema parity | Models, migrations, runtime tables, columns, constraints, indexes, and foreign keys agree. | FAIL |
| Documentation truthfulness | API/model docs and current status match the revision. | PASS IN WORKTREE / PENDING IMMUTABLE REVISION |
| Supply-chain/container checks | Required image and dependency checks execute and pass. | NOT PROVEN |

## Mandatory environment evidence

For every production target, attach evidence for:

1. Rendered and applied deployment configuration tied to an immutable revision.
2. Secret injection and rotation without committed credentials.
3. TLS, ingress, rate limiting, and network policy validation.
4. Database migration execution and schema parity in the target dialect.
5. Backup integrity, timed restore, replay validation, and operator sign-off.
6. Provider failure, worker failure, queue recovery, and rollback drills.
7. Load, latency, resource, and capacity tests against declared objectives.
8. Observability, alert routing, degraded-state visibility, and incident handling.
9. Security review, dependency/container scanning, and penetration testing.
10. Keyboard, screen-reader, responsive-layout, and automated accessibility review.

## Capability-specific requirements

### Wallet/LNURL

The foundation is not a production feature until routers, dependencies, policy,
revocation, audit, SDK/frontend contracts, negative tests, and deployment
configuration are connected and evidenced. Until then it must be described as
foundation-only.

### Reflex frontend

Static route registration is insufficient. Production evidence must include a
successful build/export, live backend integration, browser tests, manual route
review, degraded/error states, and accessibility results. Delegated Jinja route
ownership must remain explicit.

### Market intelligence and Trace

Outputs must remain informational and uncertainty-aware. Historical similarity,
candle attribution, privacy analysis, evidence packets, and Trace findings are
not predictions, legal verdicts, compliance certification, or Bitcoin consensus
proof.

## Promotion procedure

1. Select an immutable commit and target environment.
2. Run mandatory repository gates and retain exact outputs.
3. Deploy through the documented profile with operator approval.
4. Run environment evidence checks and drills.
5. Review limitations, unresolved risks, rollback readiness, and evidence
   integrity.
6. Record an explicit promote/hold decision with owners and artifact references.

Any mandatory failure results in **HOLD**. Missing evidence is not a pass.

## Current blockers

The authoritative blocker list is maintained in [STATUS.md](STATUS.md). At the
last verification, CI, code quality, integration tests, and schema parity were
failing, and production environment evidence was absent. Documentation
truthfulness passes in the current working tree but must be committed and pass
again for the selected release revision.
