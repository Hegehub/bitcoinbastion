# Single-node runtime overlay

## Purpose

This overlay adapts the canonical `deploy/kubernetes/base` manifests for constrained one-node Kubernetes deployments with reduced resource requests, single replicas, neutralized autoscaling, and suspended heavy recurring jobs.

## Best for

- Constrained VPS deployments.
- Home servers and small sovereign self-hosted environments.
- Operators who understand and accept one-node availability limits.

## Not suitable for

- High availability.
- Production-equivalent claims compared with full multi-node Kubernetes.
- Unattended heavy market-intelligence, evidence, or recovery workloads on weak hardware.
- Operators without monitoring, backups, recovery drills, and rollback discipline.

## Minimum suggested resources

- 2 vCPU minimum; 4 vCPU recommended.
- 4 GiB RAM minimum; 8 GiB recommended when enabling suspended jobs manually.
- Reliable disk and explicit backup process.

## Production suitability

Single-node mode may be acceptable for sovereign small production only with operator awareness, explicit backups, monitoring, and recovery evidence. Single-node mode is not highly available and must not be presented as equivalent to full production Kubernetes.

## HA limitations

The overlay forces API, worker, and beat replicas to 1. A node failure is a service outage. This profile does not provide HA, disaster recovery, or automatic capacity scaling by itself.

## Evidence limitations

Evidence jobs remain available from the base, but heavy recurring evidence and intelligence CronJobs are suspended by default. Run them manually or re-enable them only after checking CPU, memory, database, Redis, and disk capacity.

## Storage notes

Single-node storage is a risk. Backups are mandatory before production claims. This overlay does not provide HA or disaster recovery by itself. External PostgreSQL and Redis remain safer for serious deployments.

## Ingress notes

This overlay inherits the base ingress. Configure your ingress controller, DNS, TLS, and reverse proxy explicitly. No cloud load balancer is assumed.

## Secrets requirements

Create `bitcoin-bastion-secrets` from a local secret manager, sealed secret, or external secret workflow. Do not commit real credentials. This profile preserves no custody. This profile does not introduce custody, seed phrase handling, private key handling, wallet file handling, or signing material handling.

## Render command

```bash
kubectl kustomize deploy/kubernetes/overlays/single-node
```

## Apply command

```bash
kubectl apply -k deploy/kubernetes/overlays/single-node
```

## Rollback notes

Use Git to revert overlay changes and `kubectl rollout undo deployment/bitcoin-bastion-api -n bitcoin-bastion-single-node` for deployment rollbacks. Validate database migrations, backups, and suspended CronJob state before rollback.

## Known limitations

- HPA is neutralized to one replica, not removed.
- Recovery drill and selected heavy recurring intelligence/evidence jobs are suspended by default.
- Provider health remains enabled because degraded/fallback/stale states must stay visible.
- Not equivalent to a production cluster.
