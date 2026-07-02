# Service mesh

Owns internal service routing, east-west traffic policy, mTLS design, sidecar policy and internal network observability.

Current canonical paths:

- Kubernetes/deployment manifests under `deploy/`
- service policy documentation under `docs/`

Migration rule: mesh features must not be required for local development unless a documented fallback exists.
