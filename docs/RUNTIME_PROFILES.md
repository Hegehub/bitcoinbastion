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

## Mandatory runtime safety statements

No runtime profile implies custody. No runtime profile requires seed/private-key handling. No runtime profile is automatically production-ready. Production readiness requires environment evidence artifacts.

## Primary commands

| Profile | Primary commands |
| --- | --- |
| `compose` | `make runtime-render-compose`; `make deploy-compose` |
| `k8s` | `make runtime-render-k8s`; `make deploy-k8s` |
| `k3s` | `make runtime-render-k3s`; `make deploy-k3s` |
| `kind` | `make runtime-render-kind`; `make deploy-kind` for local validation only |
| `minikube` | `make runtime-render-minikube`; `make deploy-minikube` for local testing only |
| `single-node` | `make runtime-render-single-node`; `make deploy-single-node` with constrained-production limitations |
| `bare-metal/systemd` | `make systemd-notes`; run systemd units manually from `docs/BARE_METAL_SYSTEMD.md` |

Each profile entry in the comparison matrix identifies best hardware, complexity, production suitability, evidence support, HA support, resource footprint, operational risk, recommended use, and limitations. Commands render or apply the existing runtime metadata and manifests; they do not create custody, cloud lock-in, seed handling, private-key handling, or automatic production certification.

## Frontend runtime modes

The runtime profile metadata now includes frontend mode information. Only two frontend modes are available because the legacy Next.js frontend and parallel migration mode have been removed.

| Mode | Best for | Ports | Services | Limitations | Production suitability |
| --- | --- | --- | --- | --- | --- |
| `api-only` | SDK/API deployments and backend only tests | `8000` | FastAPI and backend dependencies | No browser frontend | Suitable for API‑only scenarios |
| `reflex` | Default and primary user interface | `8000`, `3001`, `8001` | FastAPI backend plus Reflex frontend | Market detail and drill‑down pages remain served by FastAPI/Jinja until Reflex achieves full parity; full production readiness still requires route/API parity, deployment evidence and operator validation | Suitable once evidence gates and parity checks pass |

Runtime metadata fields include `frontend.mode`, `frontend.primary`, `reflex_enabled`, `cutover_ready` and `rollback_available`. With the legacy frontend removed, `frontend.primary` is now `reflex`, `reflex_enabled` is `true`, and `rollback_available` is `false` because restoring the deleted frontend requires retrieving it from version control.

No frontend mode may request seed phrases, private keys, wallet files, keystore files, signing material, or custody services.
