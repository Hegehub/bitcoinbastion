# Legacy Next.js Frontend Status

Status: **legacy rollback frontend retained in place**.

Reflex is the preferred primary migration frontend, but the Next.js frontend remains in `frontend/` to preserve rollback while final production evidence is gathered.

## Why this remains

- Rollback still depends on a working Next.js surface.
- Market detail route ownership remains delegated/partial.
- Root-suite and Docker-local blockers remain outside the Reflex-local checks.
- Maintainers have not explicitly approved a physical archive/move/delete of `frontend/`.

## Reflex primary path

- Reflex app: `reflex_frontend/`
- Runtime selector: `BASTION_PRIMARY_FRONTEND=reflex`
- Legacy selector: `BASTION_LEGACY_FRONTEND=nextjs`

## Last verified commands

- `cd frontend && npm install`
- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run test`
- `cd frontend && npm run build`

These passed in Prompt 22/22 with existing npm audit/config warnings.

## Rollback notes

Set `BASTION_PRIMARY_FRONTEND=nextjs`, run the legacy frontend, and keep FastAPI/Jinja Market routes active. See `docs/FRONTEND_ROLLBACK_PLAN.md`.
