# Runtime Profiles

Bitcoin Bastion supports multiple self-hosted deployment profiles. Kubernetes is supported, but Kubernetes is not mandatory for every operator or every environment. Docker Compose remains supported for local development, tiny VPS deployments, simple demos, and operator testing.

Runtime profiles describe deployment posture and limitations. They do not change Bitcoin Bastion's no-custody posture: no profile authorizes seed phrase handling, private key handling, wallet file handling, signing material handling, transaction signing, transaction broadcasting, or automatic risky execution.

## Operating principles

- Kubernetes is optional; `deploy/kubernetes` is the canonical Kubernetes manifest path when Kubernetes is used.
- Docker Compose remains a supported runtime for development and small self-hosted tests.
- K3s is the recommended Kubernetes-flavored path for sovereign small deployments such as a VPS, home server, or mini-PC, once the planned overlay is implemented and hardened.
- Standard Kubernetes is recommended for larger production clusters with mature ingress, storage, monitoring, secret-management, backup, and operational processes.
- Kind and Minikube are local testing profiles, not production profiles.
- Bare-metal/systemd is an advanced fallback profile for operators who accept manual process supervision and hardening work.
- Single-node deployments are possible, but they have explicit availability, scaling, and operational limitations.
- No runtime profile requires cloud provider lock-in.
- Full release-candidate or production claims still require environment-specific evidence artifacts, backup/restore evidence, monitoring validation, secrets handling validation, and operational drills.

## Profile comparison matrix

| Profile | Best hardware / best fit | Complexity | Production suitability | Evidence support | HA support | Resource footprint | Operational risk | Recommended use | Key limitations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `compose` | Laptop, dev workstation, tiny VPS | Low | Limited | Partial/manual | No | Low to medium | Medium | Local development, simple demos, tiny VPS, operator testing | Not HA; manual scaling; weaker isolation than Kubernetes; evidence collection may be partial or manual. |
| `k8s` | Multi-node Kubernetes cluster or mature self-hosted cluster | High | Strongest when operated correctly | Strong | Strong | Medium to high | High if operated without Kubernetes expertise | Staging and larger production clusters | Requires Kubernetes expertise; production readiness depends on real environment validation; secrets, ingress, storage, monitoring, and backup must be configured by the operator. |
| `k3s` | Sovereign VPS, home server, mini-PC, small cluster | Medium | Good for small sovereign deployments when properly hardened | Strong | Possible, but not guaranteed by default | Low to medium | Medium | Small self-hosted production and staging with the K3s overlay | Single-node K3s has no HA; not production-equal to a well-operated multi-node Kubernetes cluster; heavy jobs may need suspension or manual execution on weak hardware. |
| `kind` | Developer laptop or CI runner | Low | None | Render-only | No | Low | Low for testing, unacceptable for production | Local manifest validation and smoke testing | Not production-ready; not a real operational environment; rendered manifests do not prove production readiness; use only for render/test compatibility. |
| `minikube` | Developer/operator workstation | Low to medium | None | Local-only | No | Medium | Low for local testing, unacceptable for production | Local operator testing, ingress experiments, and developer demos | Not production-ready; local testing only; does not include production TLS/WAF/CDN, HA, or disaster recovery evidence; depends on local machine resources. |
| `single-node` | Constrained VPS or home server | Medium | Conservative / limited | Partial to strong, depending on instrumentation | No | Low to medium | Medium to high | Sovereign minimal production only with accepted limitations and the single-node overlay | No HA; lower resource limits; heavy jobs are suspended or should be manual; not equivalent to a production cluster; backups, monitoring, recovery drills, and operator discipline are required. |
| `bare-metal/systemd` | Bare-metal host, VM, or advanced fallback machine | High/manual | Possible but manual | Manual | Manual | Low to medium | High | Advanced operators and fallback deployments | Manual service supervision, logs, backups, monitoring, env files, migrations, health checks, and hardening; no Kubernetes-native NetworkPolicy, PDB, HPA, or ServiceMonitor. |

## Canonical Kubernetes path

`deploy/kubernetes` remains the canonical Kubernetes deployment path. The runtime profile metadata under `deploy/runtime-profiles` references that path; it does not replace it and does not introduce a new canonical `k8s/` directory.

## Planned overlays

K3s, single-node, Kind, and Minikube baseline overlays now exist under `deploy/kubernetes/overlays`. Kind is for local manifest validation and smoke testing. Minikube is for local operator testing and ingress experiments. Neither Kind nor Minikube is production-ready, and neither profile proves production readiness.

## Evidence and readiness

Runtime profile metadata improves deployment clarity, but metadata alone is not production evidence. Operators must still collect environment-specific artifacts for secrets management, TLS, ingress, storage, backups, monitoring, alerting, recovery drills, and degraded-state visibility before making production-readiness claims.
