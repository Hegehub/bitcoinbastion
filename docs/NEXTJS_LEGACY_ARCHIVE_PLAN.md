# Legacy Frontend Archive Plan

Date: 2026-06-29

## Decision

The old Next.js frontend has been removed from the working tree at maintainer request. Reflex is now the only repository-native frontend under `reflex_frontend/`.

## Removed paths

- `frontend/`
- `.github/workflows/frontend-ci.yml`
- `deploy/compose/full-parallel-frontends.compose.yaml`

## Current frontend ownership

- Reflex owns the repository-native public, Trace, Console, and preview Market frontend surfaces.
- FastAPI remains the backend source of truth.
- FastAPI/Jinja still owns delegated Market detail/dashboard routes.

## Rollback limitation

Rollback to the old frontend requires restoring deleted files from Git history or a tagged archive. Do not claim an in-tree runnable old frontend exists after this cleanup.

## Remaining blockers

This removal does not by itself prove broad production readiness. Root pytest, root lint, docs-truthfulness, Docker/runtime verification, and historical documentation cleanup still require follow-up work.
