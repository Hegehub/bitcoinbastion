# Runtime Profile Metadata Contract

Lifecycle: **ACTIVE REFERENCE**
Canonical deployment guide: [DEPLOYMENT_METHODS.md](DEPLOYMENT_METHODS.md)

This document defines the boundary between the human deployment guide and the
machine-readable runtime metadata. Choose and execute a deployment from the
canonical guide; use the files under `deploy/runtime-profiles/` when inspecting
or extending profile detection and render/apply behavior.

Kubernetes is supported; Kubernetes is not mandatory. All profiles preserve the
Bitcoin Bastion no-custody boundary and do not authorize seed phrases, private
keys, wallet files, signing material, transaction signing, or broadcasting.

## Metadata sources

| Profile | Metadata | Artifact owner |
| --- | --- | --- |
| Compose | `deploy/runtime-profiles/compose.yaml` | `docker-compose.yml` |
| Kubernetes | `deploy/runtime-profiles/k8s.yaml` | `deploy/kubernetes` |
| K3s | `deploy/runtime-profiles/k3s.yaml` | `deploy/kubernetes/overlays/k3s` |
| Kind | `deploy/runtime-profiles/kind.yaml` | `deploy/kubernetes/overlays/kind` |
| Minikube | `deploy/runtime-profiles/minikube.yaml` | `deploy/kubernetes/overlays/minikube` |
| Single-node | `deploy/runtime-profiles/single-node.yaml` | `deploy/kubernetes/overlays/single-node` |
| Bare-metal/systemd | `deploy/runtime-profiles/bare-metal-systemd.yaml` | `docs/BARE_METAL_SYSTEMD.md` |

`deploy/kubernetes` is the canonical Kubernetes path. Runtime metadata points to
that tree; it does not replace the manifests or create a second Kubernetes
source of truth.

K3s is the recommended Kubernetes-flavored option for sovereign small deployments only after operator hardening and evidence collection.

Kind is for local manifest validation and smoke testing. Minikube is for local operator testing and ingress experiments. Kind and Minikube are not production deployment methods. Neither Kind nor Minikube is production-ready, and neither profile proves production readiness.

## Contract enforced by tests

Every profile metadata file declares identity, runtime type, status, intended
environments, resource expectations, HA and evidence capabilities, canonical
paths, commands, limitations, security notes, and evidence notes. The aggregate
`deploy/runtime-profiles/profiles.yaml` preserves the common safety constraints.

The helper defaults to dry-run; apply requires explicit confirmation and real
runtime tooling. Production readiness requires environment evidence artifacts.
Rendering metadata or manifests is never production evidence by itself.
