# Prompt 15R — inherited verification closure

## Repository and environment

Verification started at `cb939424e00a9815f695db6e29f10fdd34ebb368` on branch
`work`, with a clean worktree and no configured Git remotes. No applicable
`AGENTS.md` exists. `gh auth status` reports no authenticated GitHub host; this is
an environment publication limitation, not an application-readiness failure.

## Verification-debt matrix

| Gate family | Canonical command/test | Prior state | Result | Action |
|---|---|---:|---|---|
| Semantic handoff / Stage-1 | `python scripts/validate_stage1_handoff.py`; `python scripts/generate_http_transport.py --check` | PASS | PASS (`VALID_UNCHANGED_SOURCE`, 219 operations, 380 schemas) | none |
| Prompt 11 | focused similarity services/frontend plus `PYTHONPATH=. python tests/browser_support/run_prompt11r_browser.py` | unverified | PASS | installed browser runtime dependencies only |
| Prompt 12 | contract/frontend tests plus `python tests/browser_support/run_prompt12_browser.py` | unverified | PASS; submit 1, duplicates 0 | none |
| Feature 53 | canonical generator check and contract ownership tests | stale hard-coded counts | PASS; zero-owner 0, duplicate-owner 0 | made assertions derive from canonical registries |
| Feature 52/54/59/60/67, routes/nav/flags/shell/mobile | complete frontend suite | partially verified | PASS, 263 tests | repaired stale contract checker ownership boundary |
| Stage-4 | focused WebSocket contract/integration/unit suites | unverified | PASS, 56 tests | none |
| Ruff | `ruff check .` and changed-file Ruff | known debt | 59 repository-wide findings; changed remediation files PASS | no unrelated cleanup |
| mypy | `mypy app frontend/bastion_ui` | known debt | repository-wide existing Reflex/type debt; no remediation-file regression | no unrelated cleanup |
| pytest | `pytest -q` and focused acceptance suites | unverified broad | 2920 pass, 3 skip, 41 fail; mandatory Prompt 11/12/15 and Feature-53 subsets PASS | fixed five stale Stage-1/Feature-53 checks; unrelated failures retained |
| Reflex export | `.venv/bin/reflex export --frontend-only` | PASS | PASS | none |
| Prompt-15 browser/a11y | `python scripts/verify_prompt14_browser.py` | PASS | PASS; four axe scans, zero privacy leaks/duplicates | none |

## Prompt 11

Canonical ownership remains Feature 18 (Historical similarity overlays), Feature
20 (Uncertainty ribbons/hatching), and Feature 47 (accessible chart/table
alternative). The focused backend suite passed 37 tests and the frontend/platform
suite passed. The real browser harness proved the protected generated transport
with ephemeral Device-bound PoP and `market:intelligence:read`, a 200 response,
backend rank/score/method, backend empirical interval `[0.54, 0.845]`, Replay
correlation, zero leaks, and zero unexpected duplicate requests. Feature 47 has no
file-export authority; its canonical export requirement is the accessible table.
Frontend uncertainty recalculation remains zero.

## Prompt 12

Canonical ownership remains Feature 21 (public Trace Submit) and Feature 22
(public advisory Report). Contract/API tests passed. The browser ledger observed
exactly one `POST /api/v1/trace/submit`, zero duplicate mutations, persisted Report
rendering, refresh and back/forward reads without resubmission, and mobile Report
rendering. Public operation metadata remains distinct from protected Similarity
and protected Prompt-13–15 reads.

## Feature 53 and generation

The source of truth is the OpenAPI snapshot plus rendering/ownership matrices,
`generated_http.OWNERSHIP`, `generated_http.FEATURE_53`, and
`generated_manifest.json`. The canonical full generator `--check` passed. Semantic
handoff evaluated source and generator fingerprints, not exact-HEAD equality. No
regeneration was required. Exactly 219 authoritative operations have 219 unique
owners and 219 unique Feature-53 registry identities. Prompt-15 lineage, replay,
verification and export operations and inherited Prompt-11–14 operations are in
the same exactly-one set.

The older foundation-only generator reports stale because it represents the
superseded two-operation bootstrap foundation; it is not the current complete
Stage-1 generator. Raw preflight remains deliberately fail-closed before reviewed
security/mutation overrides; its test now checks internal partition consistency
and the explicit reviewed-operation blocker set rather than obsolete 194-operation
counts.

## Platform and broad-test classification

The complete frontend suite passed 263 tests, covering Feature 52/54/59/60/67,
routes, navigation, flags, shell, command palette, mobile shell, and Prompt-15
adapters/state. Stage-4 passed 56 tests. Route/API parity and runtime-profile checks
passed; Kubernetes rendering was skipped only because `kubectl` is unavailable.
The frontend contract validator now checks command derivation from canonical route
metadata rather than requiring duplicated literal paths in the presentation-only
palette.

The broad backend run produced 2920 passes, 3 skips and 41 failures. Twelve MCP
async failures were environment-only and passed (21 tests) after installing the
project-declared `pytest-asyncio` dependency. Five stale generated-count/schema
failures were repaired and their 12-test contract set passes. Remaining failures
are unrelated pre-existing security-expectation, SDK wording, legacy DB-isolation,
and LNURL clock-sensitive tests outside Prompt 11–15; mandatory focused gate suites
remain green. Repository-wide Ruff/mypy findings likewise predate this remediation
and changed remediation files pass Ruff.

## Prompt-15 regression

The browser rerun preserved current and A/B historical packets, late-response
isolation, lineage, replay MATCH, scoped identity-integrity verification, safe ID
copy, backend JSON export, exact historical identity, mobile/reduced-motion/theme
behavior, and request deduplication. Privacy canary occurrences were zero in HTTP,
DOM/ARIA and export. Axe reported zero violations for current packet, historical
packet, Evidence detail and mobile Evidence lineage.

## Rollback

Rollback only this remediation's contract-checker and test expectation updates.
That restores the stale literal-path and 194/286-count assumptions but does not
change generated transport, Prompt-11/12 behavior, Evidence lineage, replay,
verification, export, privacy, Prompt-13/14, D1/D2, T1–T4, G1–G4, snapshots, Trace
Submit/Report, Evidence records or user data.
