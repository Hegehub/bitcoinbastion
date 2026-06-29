# Next.js Legacy Archive Plan

## Archive decision

Decision: **B. Mark Next.js as legacy but keep in `frontend/`.**

The physical archive/move/delete gate does not pass yet. Reflex is the preferred primary migration frontend, but Next.js must remain intact for rollback because root-suite blockers remain, Docker was not locally verified, formal accessibility audit is incomplete, and Market detail ownership remains delegated to FastAPI/Jinja.

## Why Next.js is not deleted

- Rollback is still required during Reflex primary stabilization.
- Market route ownership is partial/delegated rather than fully Reflex-owned.
- Legacy Next.js install, lint, typecheck, tests, and build currently pass, so keeping it is low-risk and useful for fallback.
- Deleting or moving it would make rollback harder without adding safety.

## Archive gate status

| Gate | Status | Notes |
| --- | --- | --- |
| Reflex route parity passes | PASS | public/Trace/Console route parity passes |
| Reflex API parity passes | PASS/PARTIAL | Market detail remains delegated |
| Trace parity passes | PASS | safety and no-custody tests pass |
| Market ownership/delegation documented | PASS | delegated routes documented |
| Reflex build/export passes | PASS | local Reflex export passed |
| CI passes | PARTIAL | Reflex CI exists; root suite still has known failures |
| rollback plan exists | PASS | rollback docs exist |
| maintainers explicitly want physical archive | NOT CONFIRMED | no explicit physical archive approval in this prompt |

## Current legacy status

- Path: `frontend/`
- Status: legacy rollback frontend
- Last verified local commands: install, lint, typecheck, test, build all passed with existing npm audit/config warnings.
- Archive location: not moved.
- Deletion: not allowed in this prompt.

## Future archive options

1. Keep `frontend/` as legacy rollback until production evidence is complete.
2. In a separate explicit cleanup PR, move `frontend/` to a legacy path only after maintainers approve physical archive.
3. Delete Next.js only in a later explicit cleanup PR after rollback no longer depends on it.

## Required evidence before physical archive

- Clean or explicitly scoped root suite.
- Reflex Docker build evidence from CI or Docker-capable host.
- Accessibility/responsive audit evidence.
- Market delegation accepted as permanent or full Reflex Market parity completed.
- Updated operational runbooks proving rollback without Next.js or with archived Next.js.

## Final destructive cleanup audit update (2026-06-28)

The final deletion prompt did not remove `frontend/`. The archive record is now captured in `docs/legacy/NEXTJS_FRONTEND_ARCHIVE.md` as a pending archive rather than a completed removal. Next.js remains legacy rollback until the full cutover blockers are cleared.

## Old frontend removal sweep update (2026-06-29)

Archive/removal remains pending. The 2026-06-29 sweep did not delete `frontend/` because repository-level verification and deployment-reference gates failed. Treat Next.js as legacy rollback, not primary development surface, until a follow-up removal PR clears the blockers in `docs/OLD_FRONTEND_REMOVAL_REPORT.md`.
