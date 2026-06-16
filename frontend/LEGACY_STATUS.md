# Next.js Legacy Frontend Status

This frontend is legacy but supported until Reflex parity is complete.

Do not delete this directory until:
- Reflex public route parity is complete.
- Reflex Trace route parity is complete.
- Reflex Market/Console ownership is resolved.
- Reflex safety and forbidden-wording tests pass.
- Reflex Docker/CI integration passes.
- rollback strategy is documented.

## Current frontend stack

- Framework: Next.js 14 App Router.
- Runtime/UI: React 18, TypeScript, Tailwind CSS, React Query provider support.
- Tests: Vitest, Testing Library, and Playwright test files.
- API access: browser-side `fetch` helpers in `frontend/services/` and `frontend/lib/api/`.

## Current responsibility

The `frontend/` tree remains responsible for the current public web frontend and Trace user workflows until Reflex reaches documented parity. It includes public pages, Trace Lite/check flows, Trace report and Proof Packet pages, navigation, command palette behavior, public API examples, and legacy/stale product and self-host pages that may be archived only after parity and rollback planning.

## Frozen expansion policy

Next.js is now **LEGACY BUT SUPPORTED UNTIL REFLEX PARITY**. It is not the target architecture for new frontend work. Keep it stable, safe, buildable, and available for rollback while Reflex is built and verified in parallel.

## Allowed changes

- [ ] safety wording fixes
- [ ] broken route fixes
- [ ] command palette stale link fixes
- [ ] API mismatch fixes
- [ ] test fixes
- [ ] build fixes
- [ ] documentation fixes

## Disallowed changes

- [ ] new major feature development
- [ ] new architecture decisions
- [ ] replacing backend logic
- [ ] deleting Trace
- [ ] deleting tests
- [ ] hiding degraded/fallback states
- [ ] adding custody/signing functionality

## Rollback role

Next.js remains the rollback frontend until Reflex is proven by route parity, API parity, safety parity, Docker/CI evidence, and a documented rollback procedure. Do not remove `frontend/` from deploy or repository paths before a separate cutover decision.

## Cutover conditions

Next.js can be archived only after:

- Reflex public route parity is complete.
- Reflex Trace route parity is complete.
- Reflex Market and Console ownership is resolved.
- Reflex safety copy, no-custody input, and forbidden-wording tests pass.
- Reflex build/export, Docker, and CI integration pass.
- API clients unwrap backend envelopes consistently.
- degraded/fallback/stale states remain visible.
- a rollback strategy is documented and tested.
