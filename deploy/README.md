# Deployment Assets

Lifecycle: **ACTIVE**

`deploy/` is the canonical owner for non-conventional deployment assets.
Repository-root `Dockerfile` and `docker-compose.yml` remain at the root because
they are standard tool entrypoints; additional deployment definitions belong
here.

## Directory ownership

| Directory | Purpose | Status |
| --- | --- | --- |
| `compose/` | Reflex and full-stack Compose variants | Active supporting |
| `helm/` | Helm metadata and values contracts | Placeholder; no installable templates |
| `kubernetes/` | Canonical Kustomize manifests, overlays, GitOps, security, observability, evidence, and operations assets | Canonical Kubernetes source |
| `runtime-profiles/` | Machine-readable runtime posture and command metadata | Active supporting |
| `scripts/` | Runtime detection, render, validation, and explicit apply helpers | Active supporting |

Do not create parallel root-level `k8s/`, `helm/`, `argocd/`, or `docker/`
trees. Kubernetes GitOps assets belong under `deploy/kubernetes/gitops/`.

Start with [`docs/DEPLOYMENT_METHODS.md`](../docs/DEPLOYMENT_METHODS.md). No
deployment asset or rendered output proves production readiness without the
revision- and environment-specific evidence defined there.
