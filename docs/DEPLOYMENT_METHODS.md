# Deployment Methods

Lifecycle: **ACTIVE — canonical deployment selection and execution guide**

Last verified against the repository: **2026-07-15**

Bitcoin Bastion has repository-backed ways to run the API, workers, and Reflex
frontend, but the repository does **not** contain evidence of a successful
production deployment. A rendered plan, an applied manifest, a green pod, or a
passing CI build is not production-readiness evidence by itself.

This document owns:

- selection of a local-run or deployment method;
- the supported command entrypoints and their source-of-truth paths;
- maturity, availability, and frontend limitations;
- minimum preflight, smoke, rollback, and evidence requirements.

The linked profile documents remain detailed runbooks. If their selection or
command guidance conflicts with this file, use this file and correct the drift.

## Choose a method

| Method | Use it for | Repository state | HA by default | Frontend | Source of truth |
| --- | --- | --- | --- | --- | --- |
| Local Python processes | Development, debugging, API and worker tests | Implemented development entrypoints; not a deployment automation path | No | FastAPI/Jinja; Reflex is a separate process | [`Makefile`](../Makefile), [`scripts/start_api.sh`](../scripts/start_api.sh), [`scripts/start_worker.sh`](../scripts/start_worker.sh), [`scripts/start_beat.sh`](../scripts/start_beat.sh) |
| Docker Compose backend stack | Local development, demos, operator smoke tests, small non-HA self-hosted experiments | Supported Compose baseline; environment-specific operation is not proven | No | FastAPI/Jinja only | [`docker-compose.yml`](../docker-compose.yml), [`compose.yaml`](../deploy/runtime-profiles/compose.yaml) |
| Docker Compose with Reflex | Full local UI stack and operator/frontend testing | Implemented Compose variant with development defaults; not a distinct runtime profile | No | Reflex on `3001`/`8001`, FastAPI on `8000` | [`full-reflex.compose.yaml`](../deploy/compose/full-reflex.compose.yaml), [Reflex runbook](REFLEX_DEPLOYMENT.md) |
| Standard Kubernetes | Staging or a multi-node self-hosted/managed cluster | Production-oriented manifest baseline; placeholders and environment evidence block an unchanged production apply | Possible when the operator supplies real resilient dependencies and cluster controls | Canonical manifests deploy API, worker, and beat, not the Reflex container | [`deploy/kubernetes`](../deploy/kubernetes/README.md), `staging` and `production` overlays |
| K3s | Sovereign VPS, home server, mini-PC, small Kubernetes installation | Overlay and apply wrapper exist; no live-environment proof; inherited image/config placeholders must be replaced | No for a one-node K3s installation | API/worker/beat; no Reflex workload | [`overlays/k3s`](../deploy/kubernetes/overlays/k3s/README.md), [`k3s.yaml`](../deploy/runtime-profiles/k3s.yaml) |
| Single-node Kubernetes | A constrained one-node installation when K3s-specific behavior is not wanted | Overlay and apply wrapper exist; no live-environment proof; inherited placeholders must be replaced | No | API/worker/beat; no Reflex workload | [`overlays/single-node`](../deploy/kubernetes/overlays/single-node/README.md), [`single-node.yaml`](../deploy/runtime-profiles/single-node.yaml) |
| Kind | Local Kubernetes render and smoke testing | Local-only overlay; never a production method | No | API/worker/beat test workloads | [`overlays/kind`](../deploy/kubernetes/overlays/kind/README.md), [`kind.yaml`](../deploy/runtime-profiles/kind.yaml) |
| Minikube | Local ingress and operator workflow testing | Local-only overlay; never a production method | No | API/worker/beat test workloads | [`overlays/minikube`](../deploy/kubernetes/overlays/minikube/README.md), [`minikube.yaml`](../deploy/runtime-profiles/minikube.yaml) |
| Bare metal/systemd | Advanced manual fallback on a Linux host | Process commands and operator notes exist; service unit files and automated apply do not | Manual only | API process; Reflex must be operated separately | [Systemd notes](BARE_METAL_SYSTEMD.md), [`bare-metal-systemd.yaml`](../deploy/runtime-profiles/bare-metal-systemd.yaml) |

Practical default choices:

- use local Python processes for backend development and debugging;
- use full Reflex Compose for an end-to-end local UI environment;
- use Kind for local Kubernetes manifest/smoke work and Minikube when local
  ingress behavior matters;
- use K3s or the single-node overlay only when the operator accepts a node
  failure becoming an outage;
- use the standard Kubernetes overlays for a serious multi-node staging or
  production target, after creating an environment-owned overlay and collecting
  all required evidence.

No method is currently certified as production-ready. The current repository
decision is maintained in [Production Readiness](PRODUCTION_READINESS.md) and
[Status](STATUS.md).

## Runtime helper contract

The helper is the common command surface for the seven runtime profiles. It is
safe to inspect and render without changing a target:

```bash
python deploy/scripts/render-runtime-profile.py --list
./deploy/scripts/bastion-deploy detect
./deploy/scripts/bastion-deploy render --profile k3s --env staging
./deploy/scripts/bastion-deploy validate --profile k3s --env staging
```

`detect` is a host-tool recommendation, not an environment certification.
`render` is a plan only. `validate` checks Compose configuration, the systemd
guide, or Kustomize rendering depending on the profile. An apply is explicit
and state-changing:

```bash
./deploy/scripts/bastion-deploy apply --profile PROFILE --env ENVIRONMENT --yes
```

Supported environments are `local`, `dev`, `staging`, and `production`.
Supported profiles are `compose`, `k8s`, `k3s`, `kind`, `minikube`,
`single-node`, and `bare-metal-systemd`. The systemd helper intentionally
refuses automatic apply; the operator must install and supervise processes.

Machine-readable profile posture lives in
[`deploy/runtime-profiles`](../deploy/runtime-profiles/README.md). That metadata
does not replace Compose files, Kustomize overlays, systemd service units, or
environment evidence.

## Local Python processes

This is the shortest development path. It runs from the checkout and is not a
repeatable host or cluster deployment.

```bash
make install-dev
cp .env.example .env
# Review .env; placeholders and local defaults are not production secrets.
make migrate
make run
```

In separate terminals, start the asynchronous processes when the behavior under
test needs them:

```bash
make worker
python -m celery -A app.tasks.celery_app.celery_app beat --loglevel=info
```

Run Reflex separately when a browser UI is needed:

```bash
make reflex-sync
cd reflex_frontend
uv run reflex run --frontend-port 3001 --backend-port 8001
```

Smoke checks:

```bash
curl --fail http://localhost:8000/health/live
curl --fail http://localhost:8000/health/ready
curl --fail http://localhost:3001/  # only when Reflex is running
```

Stop foreground processes with `Ctrl-C`. This path has no HA, host hardening,
backup automation, service restart policy, or deployment rollback artifact.

## Docker Compose backend stack

The canonical backend Compose file starts PostgreSQL, Redis, MinIO bucket
bootstrap, API, worker, and beat. It does not start Reflex.

Preflight and render:

```bash
cp .env.example .env
# Replace required local placeholders in .env; never commit the result.
docker compose --env-file .env config
make runtime-render-compose
./deploy/scripts/bastion-deploy validate --profile compose --env local
```

Apply and verify:

```bash
make deploy-compose
docker compose ps
curl --fail http://localhost:8000/api/v1/health/live
curl --fail http://localhost:8000/api/v1/health/ready
```

The equivalent production-mode entrypoint is:

```bash
ENVIRONMENT=prod docker compose --env-file .env up -d --build
```

`production` here selects application configuration; it does not make a
single-host stack highly available or production-validated. The Compose file
contains local MinIO defaults and host-bound volumes. Before any serious
self-hosted use, replace defaults, add TLS/reverse proxy controls, persistent
backup and restore, monitoring, log retention, secret rotation, and a tested
host recovery procedure.

Stop without deleting volumes:

```bash
docker compose down
```

Rollback means checking out or building a previously verified revision/image,
then re-running Compose after confirming database migration compatibility. Do
not add `--volumes` to a routine rollback.

## Docker Compose with Reflex

Use the full stack for local end-to-end UI work:

```bash
docker compose -f deploy/compose/full-reflex.compose.yaml config
docker compose -f deploy/compose/full-reflex.compose.yaml up -d --build
docker compose -f deploy/compose/full-reflex.compose.yaml ps
curl --fail http://localhost:8000/api/v1/health/live
curl --fail http://localhost:3001/
```

Stop it with:

```bash
docker compose -f deploy/compose/full-reflex.compose.yaml down
```

This file starts PostgreSQL, Redis, API, worker, beat, and Reflex. It does not
start the MinIO/object-storage services from the canonical backend Compose file
and it uses a local default PostgreSQL password unless overridden. It is a
development/operator-test composition, not a production topology.

The frontend-only variant is useful only when a backend is already reachable:

```bash
docker compose -f deploy/compose/reflex-frontend.compose.yaml config
docker compose -f deploy/compose/reflex-frontend.compose.yaml up -d --build
```

## Kubernetes preflight shared by all overlays

[`deploy/kubernetes`](../deploy/kubernetes/README.md) is the only canonical
Kubernetes tree. The top-level `k8s/` tree is a legacy/parallel baseline and must
not be used as a second source of truth.

Before applying any canonical overlay:

1. Build and publish the selected repository revision as an immutable image.
2. Create an environment-owned Kustomize layer that replaces every sample image
   reference, hostname, storage endpoint/region, and other placeholder.
3. Supply `bitcoin-bastion-secrets` through External Secrets, Sealed Secrets,
   SOPS, Vault, a cloud secret manager, or an equivalent operator-controlled
   mechanism. Never apply `base/secret.example.yaml` unchanged.
4. Provision reachable PostgreSQL, Redis, and S3-compatible object storage as
   required. The canonical base does not deploy PostgreSQL or Redis, and its
   MinIO manifest is an unreferenced example.
5. Configure ingress class, DNS, TLS, NetworkPolicy/RBAC, monitoring, backups,
   and restore/rollback ownership.
6. Render to a file and reject unresolved placeholders or mutable application
   image tags:

```bash
kubectl kustomize PATH_TO_ENVIRONMENT_OVERLAY > /tmp/bitcoin-bastion-rendered.yaml
! rg -n 'your-org|replace-with|replace-me|example\.com|bitcoin-bastion:latest' \
  /tmp/bitcoin-bastion-rendered.yaml
kubectl apply --dry-run=server -f /tmp/bitcoin-bastion-rendered.yaml
```

The repository overlays do not pass this placeholder check unchanged. The
`apply` commands below are therefore executable entrypoints, not permission to
apply an uncustomized overlay.

After an apply, do not call the environment healthy until all of these are
visible:

```bash
kubectl -n NAMESPACE rollout status deployment/bitcoin-bastion-api
kubectl -n NAMESPACE rollout status deployment/bitcoin-bastion-worker
kubectl -n NAMESPACE rollout status deployment/bitcoin-bastion-beat
kubectl -n NAMESPACE get pods,svc,ingress
kubectl -n NAMESPACE port-forward svc/bitcoin-bastion-api 8000:8000
curl --fail http://localhost:8000/health/startup
curl --fail http://localhost:8000/health/live
curl --fail http://localhost:8000/health/ready
```

The root health routes match the canonical Kubernetes probes. A liveness pass
does not replace readiness, migration, worker, provider, storage, or evidence
checks.

## Standard Kubernetes

Use the environment overlays directly for explicit staging and production
control:

```bash
make k8s-render-staging
make k8s-render-production
```

The repository entrypoints below apply the repository overlays exactly as they
exist. Use them only after the required environment customization has been
incorporated into those paths:

```bash
make k8s-apply-staging
make k8s-apply-production
# Equivalent production wrapper:
make deploy-k8s
```

If customization lives in a separate downstream overlay, apply that path
instead of the Make targets:

```bash
kubectl apply -k PATH_TO_ENVIRONMENT_OVERLAY
```

Namespaces are `bitcoin-bastion-staging` and `bitcoin-bastion-prod`. Verify the
chosen namespace explicitly:

```bash
kubectl -n bitcoin-bastion-staging get deploy,po,svc,ingress,pdb
kubectl -n bitcoin-bastion-prod get deploy,po,svc,ingress,pdb
```

Do not use `make k8s-status` as the only check: that target currently queries
`bitcoin-bastion`, while the staging and production overlays rewrite the
namespace.

The standard Kubernetes baseline can support multiple replicas, PDB, HPA,
NetworkPolicy, ServiceMonitor, jobs, and CronJobs. It is not HA merely because
those objects render: PostgreSQL, Redis, object storage, ingress, cluster,
availability-zone, and operator choices determine real resilience. The
canonical manifests do not deploy the Reflex frontend.

See [Kubernetes Operations](KUBERNETES.md), the
[operator command lock](KUBERNETES_OPERATOR_RUNBOOK_LOCK.md), and
[production operations](KUBERNETES_PRODUCTION_OPERATIONS.md) after choosing
this method.

## K3s

K3s is the recommended Kubernetes-flavored option for sovereign small
deployments when the operator needs Kubernetes behavior and accepts the
single-node limitations. It commonly uses Traefik and local-path storage; both
must be verified rather than assumed.

```bash
make runtime-render-k3s
./deploy/scripts/bastion-deploy validate --profile k3s --env production
# This applies the repository overlay; use it only after that path passes preflight:
make deploy-k3s
kubectl -n bitcoin-bastion-k3s get pods,svc,ingress
```

For a separate downstream overlay, replace `make deploy-k3s` with
`kubectl apply -k PATH_TO_ENVIRONMENT_OVERLAY`.

Suggested minimum is 2 vCPU and 4 GiB RAM; 4 vCPU and 8 GiB are recommended for
evidence and market-intelligence jobs. The overlay forces the main workloads to
one replica and neutralizes the API HPA to one. A one-node K3s installation is
not HA. External PostgreSQL and Redis are safer for serious use; local-path
storage needs explicit backup and restore evidence.

Application rollback entrypoint:

```bash
kubectl -n bitcoin-bastion-k3s rollout undo deployment/bitcoin-bastion-api
kubectl -n bitcoin-bastion-k3s rollout status deployment/bitcoin-bastion-api
```

Also revert the environment overlay in Git and re-apply it so live state and
declared state converge. Never roll application code back across an
incompatible database migration without a migration-specific plan.

## Single-node Kubernetes

Use this overlay for a constrained Kubernetes installation without K3s-specific
Traefik assumptions:

```bash
make runtime-render-single-node
./deploy/scripts/bastion-deploy validate --profile single-node --env production
# This applies the repository overlay; use it only after that path passes preflight:
make deploy-single-node
kubectl -n bitcoin-bastion-single-node get pods,svc,ingress
```

For a separate downstream overlay, replace `make deploy-single-node` with
`kubectl apply -k PATH_TO_ENVIRONMENT_OVERLAY`.

The overlay sets API, worker, and beat to one replica, neutralizes HPA, and
suspends selected heavy CronJobs. A node failure is a service outage. Enabling
suspended jobs requires an explicit CPU, memory, database, Redis, and disk
capacity review.

```bash
kubectl -n bitcoin-bastion-single-node rollout undo deployment/bitcoin-bastion-api
kubectl -n bitcoin-bastion-single-node rollout status deployment/bitcoin-bastion-api
```

As with K3s, reconcile the rollback through Git and validate migration
compatibility.

## Kind

Kind is a local Kubernetes test method, never a production method. Start or
select a Kind cluster before using the repository overlay:

```bash
kind create cluster --name bitcoin-bastion
kubectl config use-context kind-bitcoin-bastion
make runtime-render-kind
make deploy-kind
kubectl -n bitcoin-bastion-kind get pods,svc,ingress
kubectl -n bitcoin-bastion-kind port-forward svc/bitcoin-bastion-api 8000:8000
```

The inherited application images and external dependencies still need local
replacements. Kind can prove renderability and local smoke behavior, not real
TLS, WAF/CDN, HA, backup/restore, disaster recovery, SLO, or production
readiness.

Cleanup:

```bash
kubectl delete namespace bitcoin-bastion-kind
kind delete cluster --name bitcoin-bastion
```

## Minikube

Minikube is a local ingress/operator test method, never a production method:

```bash
minikube start
minikube addons enable ingress
make runtime-render-minikube
make deploy-minikube
kubectl -n bitcoin-bastion-minikube get pods,svc,ingress
minikube tunnel
```

The inherited application images and external dependencies still need local
replacements. Minikube evidence is local-only and cannot establish HA,
production TLS/WAF/CDN, backup/restore, disaster recovery, or runtime SLOs.

Cleanup:

```bash
kubectl delete namespace bitcoin-bastion-minikube
minikube stop
```

## Bare metal/systemd

The repository documents the process topology but does not ship installable
`.service` unit files. The helper therefore renders and validates notes but
refuses automatic apply:

```bash
./deploy/scripts/bastion-deploy render --profile bare-metal-systemd --env production
./deploy/scripts/bastion-deploy validate --profile bare-metal-systemd --env production
```

The operator must provision PostgreSQL and Redis, install the checkout or an
immutable package/image, load secrets outside Git, run migrations, and create
least-privilege units for these process commands:

```bash
python -m alembic upgrade head
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
python -m celery -A app.tasks.celery_app.celery_app worker --loglevel=info
python -m celery -A app.tasks.celery_app.celery_app beat --loglevel=info
```

Until unit files, user/file permissions, restart policy, log rotation, firewall,
TLS proxy, monitoring, backup/restore, and rollback have been supplied and
tested by the operator, this is a documented fallback rather than a repeatable
production deployment.

## Delivery mechanisms, placeholders, and non-methods

These repository surfaces must not be counted as additional deployment methods:

| Surface | Classification | Reason |
| --- | --- | --- |
| `deploy/kubernetes/gitops/` | Optional delivery/governance layer on standard Kubernetes | Argo CD application examples and promotion policy do not create a cluster, publish an application image, supply secrets, or prove a sync. Production sync is manual by default. |
| `.github/workflows/gitops-promotion.yml` | Pull-request validation gate | It lints, tests, renders overlays, and checks for a digest string; it does not apply to a cluster. |
| `.github/workflows/container-security.yml` | Build/security evidence | It builds/scans a local image but does not publish a deployable image. |
| `.github/workflows/deploy.yml` | Non-operational Reflex Cloud template | It references the absent `my-app-folder`, generic example secrets, and an unpinned third-party action tag. It is not a verified deployment path. |
| `helm/bitcoin-bastion/` | Values-only placeholder, not an installable chart | It has `Chart.yaml` and `values.yaml` but no templates, so `helm install` cannot create the application workloads. |
| top-level `k8s/` | Legacy/parallel baseline | Canonical Kubernetes ownership is `deploy/kubernetes`; using both creates drift. |
| `deploy/runtime-profiles/*.yaml` | Profile metadata | Metadata describes posture and commands; it does not deploy services. |
| Render/dry-run output | Validation artifact | Rendering proves neither successful apply nor runtime health. |
| Reflex image or frontend-only Compose | Frontend component | It requires a reachable FastAPI backend and its dependencies. |
| Temporal | Not integrated as a deployment/runtime system | No Temporal SDK, server, worker, workflow, or deployment configuration is present. `app/services/intelligence/temporal_correlation.py` is an in-process time-correlation algorithm, not Temporal.io. |
| MagicPath | Not a runtime dependency or deployment system | No MagicPath integration is present in application, deployment, CI, or runtime profile sources; it is external design/component tooling. |

GitOps may be adopted after the environment overlay and immutable image pipeline
exist. Bootstrap and promotion details then live in
[`deploy/kubernetes/gitops`](../deploy/kubernetes/gitops/README.md). It remains a
delivery mechanism for the standard Kubernetes method, not an eighth runtime
profile.

## Production promotion and evidence

All methods preserve Bitcoin Bastion's no-custody boundary. A deployment must
never receive, store, derive, transmit, log, or sign with a user's seed phrase,
wallet private key, `xprv`, or wallet file.

For a named immutable revision and target environment, promotion remains on
**HOLD** until the operator records all of the following:

1. repository tests, lint/type checks, contract checks, migration checks,
   schema parity, documentation truthfulness, and supply-chain checks pass;
2. the exact rendered and applied configuration is attached to the revision;
3. secret injection and rotation, TLS, ingress, rate limiting, network policy,
   and image provenance are verified without committed credentials;
4. migrations and target-dialect schema parity pass before normal workloads;
5. startup, liveness, readiness, worker/beat, provider, storage, and degraded
   states are observed in the target;
6. backup integrity, timed restore, evidence replay, and retention are tested;
7. provider/queue/worker failure, rollback, and incident drills pass;
8. load/capacity, observability, alert routing, security, and accessibility
   evidence is reviewed and signed off by the operator.

Use [Deployment Evidence Pack](DEPLOYMENT_EVIDENCE_PACK.md),
[Storage Deployment](STORAGE_DEPLOYMENT.md),
[Deployment Security](DEPLOYMENT_SECURITY.md), and
[Deployment Failure Runbook](RUNBOOK_DEPLOYMENT.md) for the detailed evidence
and failure procedures. Missing or stale evidence is a failure, not an implicit
pass.
