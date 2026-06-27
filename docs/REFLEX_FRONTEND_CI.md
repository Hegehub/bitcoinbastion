# Reflex Frontend CI

## 1. Purpose

The Reflex frontend CI workflow verifies that `reflex_frontend/` remains linted, typed, tested, exportable, Docker-buildable in CI, and protected by safety/route-parity checks before any primary frontend cutover.

CI passing does not by itself mean Reflex is production-primary. The primary frontend switch is controlled by Prompt 21/22 cutover gates.

## 2. CI jobs

The workflow `.github/workflows/reflex-frontend.yml` defines these jobs:

1. `reflex-quality` — installs with `uv`, runs Ruff and mypy.
2. `reflex-tests` — runs the full Reflex pytest suite.
3. `reflex-export` — runs `uv run reflex export` with non-secret `BB_` defaults.
4. `reflex-docker-build` — builds `reflex_frontend/Dockerfile` with Docker on GitHub-hosted Linux runners.
5. `frontend-safety-checks` — runs forbidden wording, no-sensitive-input, Trace safety, Market safety, Console safety, and public forbidden-wording tests.
6. `route-parity-checks` — runs public route, navigation, command-palette, Market route, Console route, and advanced Console route tests.

## 3. Local equivalent commands

```bash
make reflex-ci
make reflex-lint
make reflex-typecheck
make reflex-test
make reflex-export
make frontend-safety-check
make frontend-route-parity
make reflex-docker-build
```

Direct Reflex commands:

```bash
cd reflex_frontend
uv sync
uv run ruff check .
uv run mypy bastion_ui
uv run pytest
uv run reflex export
```

## 4. What each job proves

- Lint/type jobs prove the checked Reflex source remains syntactically and type-shape compatible with the configured tooling.
- Test jobs prove route registry, navigation, command palette, API client, Trace safety, no-custody, forbidden wording, Market route, and Console route checks pass.
- Export proves Reflex can produce an export/build artifact under CI-like settings.
- Docker build proves the committed Dockerfile can build in a Docker-enabled CI runner.
- Safety jobs prove the migration keeps no-custody and advisory wording guardrails in place.
- Route parity jobs prove the required Reflex route surface remains represented by tests and registries.

## 5. What each job does not prove

- CI does not make Reflex the primary frontend.
- CI does not delete or replace Next.js.
- CI does not replace the FastAPI/Jinja Market dashboard.
- CI does not prove production readiness, traffic cutover, load tolerance, WAF/CDN posture, or real provider availability.
- Docker build does not prove runtime readiness without deploy-time health and observability evidence.

## 6. Required environment variables

CI uses non-secret defaults only:

```env
BB_API_BASE_URL=http://localhost:8000
BB_PUBLIC_SITE_MODE=true
BB_ENABLE_TRACE=true
BB_ENABLE_TIME_MACHINE=true
BB_ENABLE_SOVEREIGN_GRID=true
BB_ENABLE_CONSOLE=true
BB_REQUEST_TIMEOUT_SECONDS=5
BB_DEFAULT_LANGUAGE=en
```

## 7. Known limitations

- `reflex export` can emit non-fatal Reflex/Node/sitemap/theme warnings; failures must not be hidden.
- The local execution environment used for Prompt 20 did not provide Docker, so Docker build was added to CI but could not be run locally.
- Legacy Next.js remains covered by `.github/workflows/frontend-ci.yml`; it is documented but not required to pass inside the Reflex-specific workflow.

## 8. Skipped checks policy

A check may be skipped locally only when the required tool is unavailable, such as Docker not being installed. The skip reason must be documented in the PR/final response and migration status. CI should still run Docker checks on GitHub-hosted runners.

## 9. Troubleshooting

- Run `uv sync` after dependency or lockfile changes.
- Run `uv run ruff check .` for lint failures.
- Run `uv run mypy bastion_ui` for type failures.
- Run `uv run pytest -vv` for test diagnostics.
- Run `uv run reflex export` locally before investigating CI-only export failures.
- Run `docker build -f reflex_frontend/Dockerfile -t bitcoin-bastion-reflex-frontend:test reflex_frontend` on a Docker-enabled machine for image issues.

## 10. Cutover relevance

Prompt 20 CI is a prerequisite for Prompt 21/22 route/API parity gates, but it is not the switch. Reflex remains a parallel migration target until the controlled primary frontend switch is explicitly completed.
