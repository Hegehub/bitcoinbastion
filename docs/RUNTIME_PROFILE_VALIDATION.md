# Runtime Profile Validation

Status: **implemented with environment validation pending**.

## Validated by Static/Smoke Checks

- Runtime metadata exists for compose, k8s, k3s, kind, minikube, single-node, and bare-metal/systemd.
- Canonical Kubernetes overlays exist under `deploy/kubernetes/overlays/`.
- Runtime scripts exist under `deploy/scripts/`.
- Makefile runtime and deployment targets call real scripts or deployment helpers.
- Render dry-runs are executed by `scripts/check_runtime_profiles.py`.

## Kubernetes Tooling

Status: **partially implemented**.

The validation script attempts `kubectl kustomize` for k3s, kind, minikube, and single-node overlays when `kubectl` is available. If `kubectl` is missing, the artifact records an explicit skipped tool limitation instead of a false pass.

## Bare-Metal/Systemd

Status: **implemented as advanced fallback documentation**.

Systemd remains an advanced fallback profile with PostgreSQL and Redis dependencies, health checks, logs, backups, migration commands, and explicit limitations. It is not the strongest high-availability path.

## Production Readiness Boundary

Rendered manifests and successful dry-runs are not production evidence. Production readiness still requires environment-specific deployment artifacts, migration smoke evidence, backup/restore drills, rollback evidence, provider health evidence, observability validation, security review, and load testing.
