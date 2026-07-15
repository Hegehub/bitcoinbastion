# Repository Layout

Lifecycle: **ACTIVE — canonical placement policy**

Last reviewed: **2026-07-15**

This document defines ownership of the repository's top-level paths. Placement
follows runtime and domain ownership; files are not moved merely to make the
tree visually smaller.

## Canonical roots

| Root | Owner and allowed contents |
| --- | --- |
| `app/` | FastAPI application, domain services, persistence, workers, providers, and delegated Jinja web surfaces |
| `artifacts/` | Retained generated validation/evidence snapshots with an identified producer; disposable output remains ignored |
| `cli/` | Installable operator CLI package; application-only seeding commands may remain under `app/cli/` |
| `config/` | Versioned non-secret runtime/domain configuration |
| `deploy/` | Compose variants, Helm placeholders, canonical Kubernetes/GitOps assets, runtime profiles, and deployment helpers |
| `docs/` | Active documentation and the explicitly historical `docs/archive/` tree |
| `mcp/` | Bastion MCP connector implementation and package metadata |
| `frontend/` | The only repository-native standalone frontend |
| `scripts/` | Repository, CI, migration, evidence, and developer command entrypoints |
| `sdk/` | Public Python and TypeScript SDK packages |
| `tests/` | Unit, integration, contract, security, deployment, SDK, and fixture coverage |

## Root-level exceptions

Standard entrypoints remain at the repository root: project/readme/license and
release documents, `.env.example`, `pyproject.toml`, lockfiles, `Makefile`,
`alembic.ini`, `Dockerfile`, and `docker-compose.yml`. External tooling expects
several of these conventional locations.

## Retired parallel roots

The following top-level directories are not allowed:

- `k8s/`: superseded, unsafe parallel baseline; Kubernetes ownership is
  `deploy/kubernetes/`;
- `argocd/`: duplicate GitOps ownership; Argo CD assets live under
  `deploy/kubernetes/gitops/`;
- `helm/`: deployment metadata belongs under `deploy/helm/`;
- `docker/`: additional container/deployment definitions belong under
  `deploy/`; the canonical backend image entrypoint is the root `Dockerfile`;
- `reflex_frontend/`: retired former name; the Reflex application now lives in
  `frontend/`;
- a second frontend root or framework-specific parallel tree: UI ownership is
  `frontend/`, while Telegram runtime ownership is `app/bot/`.

`tests/deployment/test_repository_layout.py` enforces these boundaries. A new
top-level root requires an ownership decision, consumers, and an update to this
document in the same change.
