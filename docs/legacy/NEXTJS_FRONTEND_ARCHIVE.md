# Legacy Frontend Archive Record

Date: 2026-06-29

## 1. Removal status

The old Next.js frontend has been removed from the working tree at maintainer request. Reflex is now the only repository-native frontend under `reflex_frontend/`.

## 2. Last known role

The deleted frontend was a legacy rollback surface during the Reflex migration. It is no longer runnable from this branch.

## 3. Replacement

The replacement frontend lives in `reflex_frontend/`. FastAPI remains the backend source of truth, and FastAPI/Jinja Market routes remain delegated where documented.

## 4. Removed paths

- `frontend/`
- `.github/workflows/frontend-ci.yml`
- `deploy/compose/full-parallel-frontends.compose.yaml`

## 5. Recovery

Recover the deleted frontend only from Git history or a tagged archive if maintainers need a rollback investigation. Do not document it as an active frontend while it is absent from the working tree.
