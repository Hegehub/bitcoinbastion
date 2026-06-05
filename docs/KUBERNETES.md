# Kubernetes Operations

Bitcoin Bastion health endpoints are Kubernetes-compatible and avoid Kubernetes-specific business logic.

## Probes

- Liveness: `GET /api/v1/health` or `GET /api/v1/health/live` verifies process, database reachability and migration visibility.
- Readiness: `GET /api/v1/health/runtime` exposes DB-backed runtime state, provider layer, scheduler/job state, signal pipeline, evidence pipeline and Telegram state.

These endpoints are compatible with Deployments, StatefulSets, CronJobs, HPAs and PodDisruptionBudgets. Readiness should be stricter than liveness so pods are not killed for recoverable provider degradation.

## Finalized resources

The base Kustomize layer includes Deployments, Services, Ingress, ConfigMap, Secret template, Jobs, CronJobs, HPA, PDB, NetworkPolicy, ServiceMonitor, migration smoke, schema parity, release evidence, provider health and recovery drill resources. Production operation cronjobs cover news fetch, BTC collection, candle generation, impact calculation, attribution refresh, source reputation refresh, news shock refresh, cleanup, and integrity verification.

API probes use `/health/startup`, `/health/live`, and `/health/ready` so startup, liveness and readiness semantics are separated for Kubernetes.

## Market Time Machine CronJobs

The operations CronJob manifest schedules exact operational jobs for news fetch/scoring/clustering, BTC price collection, candle building, price impact calculation, attribution, pattern/similarity refresh, shock index, signal creation/publication, evidence generation/integrity scans and operations health/cleanup snapshots.
