# Roadmap

Lifecycle: **ACTIVE**

Last reviewed: **2026-07-15**

This roadmap orders future work by dependency and release risk. Current status
lives in [STATUS.md](STATUS.md). Work items should move to GitHub Issues when
they receive an owner and acceptance criteria.

## P0 — Restore trust in `main`

### CI and branch protection

- Fix JavaScript dependency setup in `release-candidate-gates`.
- Resolve the current unit-test NameError, Ruff findings, and MyPy findings.
- Update Proof-of-Access integration fixtures and expectations.
- Require quality, test, release, schema, and docs gates before merge.

Exit evidence: a clean required-check run on the selected `main` revision.

### Migration and schema truth

- Replace model-import-driven revisions 0065–0066 with explicit, reproducible
  Alembic operations or approve a documented validator contract that provides
  equivalent historical safety.
- Resolve column, nullability, index, unique-constraint, and foreign-key parity.
- Prove bootstrap, upgrade, downgrade where supported, and replay on the target
  database dialect.

Exit evidence: all migration and runtime parity gates pass from a clean store.

## P1 — Close product and contract ambiguity

### Wallet-first and LNURL

Choose and document one of two states:

1. **Foundation-only:** keep routes disabled and label the capability accurately;
   or
2. **Activated:** complete router, dependency, policy, recovery/revocation,
   audit/event, SDK, frontend, and deployment wiring with negative tests.

### Documentation truth

- Keep the now-synchronized API/model references covered by the truthfulness gate.
- Prefer generated OpenAPI/model inventories where they can preserve explanatory context.
- Keep one current `STATUS`, one readiness contract, one deployment-method guide, and one roadmap.
- Preserve lifecycle metadata and archive conditions for temporary migration reports.

### Frontend ownership

- Update route-parity tooling to inspect dynamic Reflex registries.
- Run the complete Reflex lint/type/test/export workflow.
- Record final ownership for Reflex and delegated FastAPI/Jinja Market routes.
- Complete browser and accessibility validation.

## P2 — Produce operational evidence

- Deploy a revision-bound staging environment.
- Execute backup/restore and deterministic replay drills.
- Exercise provider, worker, queue, database, and notification failures.
- Run load/capacity tests and define measurable service objectives.
- Validate alert routing, rollback, incident records, and evidence retention.
- Complete security and accessibility reviews.

Exit evidence: an environment-specific evidence pack reviewed by an operator.

## P3 — Maintainability

- Split the largest service and route modules along existing domain boundaries.
- Review placeholder, compatibility, unused-import/dependency, and orphan-test
  candidates before removal.
- Reduce documentation orphaning through the canonical
  [documentation index](INDEX.md).

## Post-release research

These items are not release commitments:

- advanced policy automation;
- richer enterprise governance integrations;
- graph-intelligence extensions;
- deeper SIEM and identity-provider integrations;
- optional semantic similarity infrastructure.

Research must remain isolated from Bitcoin custody, signing, consensus, and
automatic-trading boundaries.
