# Repository Status

Lifecycle: **ACTIVE**

Last verified: **2026-07-15**

Verification base: `9d512e793bbe77ec06321154c03f75fccdbd7c73`

Working-tree scope: documentation lifecycle cleanup, deployment-method
consolidation, and API/model reference synchronization. These remediations must
be committed before they can serve as immutable release evidence.

This is the canonical current-state document. Historical audits, migration
reports, and former readiness claims live under `docs/archive/` and are not
current guidance.

## Overall classification

**Development baseline with implemented subsystems and failing integration
gates. Not release-candidate and not production-ready.**

No percentage readiness estimate is used. Readiness is determined by explicit
passing gates and environment evidence.

## Verification snapshot

| Surface | Result | Evidence |
| --- | --- | --- |
| Focused Proof-of-Access gate | PASS | 120 tests passed locally. |
| Focused Wallet/LNURL tests | PASS | 207 tests passed locally. |
| Full pytest | FAIL | 1,905 passed, 25 failed, 3 skipped in the audited environment. Two failures were environment-specific SOCKS proxy failures and passed with proxy variables removed. |
| GitHub CI for merged PR #149 | FAIL | 2 of 6 primary jobs passed; release-candidate, unit, integration, and quality jobs failed. |
| Ruff | FAIL | Two deterministic findings. |
| MyPy (`app`, `cli`) | FAIL | Ten findings in the latest migration implementation. |
| Alembic replay | PARTIAL PASS | Replay reaches revision `20260712_0066` and materializes 164 tables. |
| Model/migration and runtime schema parity | FAIL | Static migration coverage and five runtime parity categories remain unresolved. |
| Documentation truthfulness | PASS IN WORKTREE | `check_docs_truthfulness.py`: 249 statically discovered routes, 159 exported models, one Core documentation heading. Runtime inspection additionally found 289 unique `/api/v1` paths / 301 operations; all are represented in the API reference. |
| Compileall | PASS | `app`, `cli`, Python SDK, MCP, and Reflex sources compile. |

These numbers describe one revision and verification environment. Re-run the
gates after any material change.

## Component status

### Backend and API

The FastAPI modular monolith, workers, PostgreSQL/Alembic layer, Redis-backed
runtime support, evidence services, Market Time Machine, Trace, Citadel, SDKs,
CLI, and MCP package are present. The generated OpenAPI surface contains 302
paths and 314 operations at the verified revision. Duplicate operation-id
warnings remain to be resolved.

### Proof-of-Access

Proof-of-Access is integrated for protected APIs. It is distinct from password
login and bearer-token authentication. Payment proof, signed access rights,
entitlements, device possession, PoP sessions, request signatures, policy,
revocation, and recovery remain separate controls.

### Wallet-first and LNURL

Wallet/LNURL domain types, models, session/device services, BIP-322 support, and
LNURL primitives are implemented and covered by focused tests. They are not yet
registered as public runtime/API routes in the generated OpenAPI document.
Current product status: **foundation implemented, user-facing capability not
activated**.

### Frontend

`reflex_frontend/` is the sole repository-native frontend. FastAPI/Jinja still
owns delegated Market routes. Static route registries and contracts exist, but
the current route-parity script does not fully understand dynamic Reflex route
registration and can report false blockers. Browser, accessibility, and live
deployment evidence remain incomplete.

### Deployment and operations

Compose, Kubernetes, K3s, Kind, Minikube, single-node, and bare-metal guidance
exists. Manifest presence or dry-run planning is not deployment proof. No
current repository artifact proves a successful production deployment,
backup/restore drill, load test, penetration test, or accessibility audit.

## Current release blockers

1. Restore green required CI on `main`.
2. Fix the release-candidate workflow so JavaScript dependencies are installed
   before TypeScript SDK tests.
3. Resolve the unit-test NameError and Ruff findings.
4. Update integration tests for Proof-of-Access without weakening authorization.
5. Replace or formally redesign migrations 0065–0066 so history does not depend
   on importing future SQLAlchemy model state.
6. Make model/migration and runtime schema parity pass.
7. Commit the documentation remediation and require its truthfulness gate in CI.
8. Collect environment-specific deployment, recovery, security, load, and
   accessibility evidence.

## Canonical follow-up documents

- [PRODUCTION_READINESS.md](PRODUCTION_READINESS.md)
- [ROADMAP.md](ROADMAP.md)
- [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md)
- [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md)
- [RELEASE_CANDIDATE_GATES.md](RELEASE_CANDIDATE_GATES.md)
- [Documentation index](INDEX.md)
