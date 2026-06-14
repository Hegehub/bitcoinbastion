# K3s runtime overlay

## Purpose

This overlay adapts the canonical `deploy/kubernetes/base` manifests for K3s-based sovereign small deployments. K3s is recommended for sovereign small deployments, VPS, home server, mini-PC, or homelab setups.

## Best for

- Sovereign VPS deployments.
- Home servers and mini-PCs.
- Homelab operators who want Kubernetes without managed-cloud lock-in.
- Small self-hosted environments that accept non-HA limitations unless the operator builds a real HA K3s cluster.

## Not suitable for

- Claims of full HA by default.
- Managed-cloud-specific assumptions.
- Workloads that require production-equal behavior with a multi-node Kubernetes production cluster.
- Operators without a backup, monitoring, secret-management, and recovery plan.

## Minimum suggested resources

- 2 vCPU minimum; 4 vCPU recommended.
- 4 GiB RAM minimum; 8 GiB recommended for evidence and market-intelligence jobs.
- External PostgreSQL and Redis are recommended for more serious deployments.

## Production suitability

This is a conservative production-oriented profile for small sovereign deployments when hardened and validated by the operator. It is not production-equal to the full multi-node Kubernetes production overlay.

## HA limitations

The overlay sets API, worker, and beat replicas to 1 and neutralizes the API HPA to a single replica. A single-node K3s deployment is not HA.

## Evidence limitations

Evidence jobs remain available from the base as manual/operator-triggered jobs. Heavy recurring evidence or recovery workflows should be run intentionally and monitored on weak hardware.

## Storage notes

K3s commonly uses the `local-path` storage class. Local storage increases operational risk and must be backed up intentionally. External PostgreSQL and Redis remain recommended for serious deployments.

## Ingress notes

K3s commonly includes Traefik. If Traefik is enabled, this overlay uses Traefik ingress annotations and `ingressClassName: traefik`. If Traefik is disabled, configure another ingress controller, port-forwarding, or a reverse proxy. Hostnames are examples only; do not commit real domains or TLS secrets.

## Secrets requirements

Create `bitcoin-bastion-secrets` using your local secret manager or sealed/external secret workflow. Do not commit real credentials. This profile preserves no custody. This profile does not introduce custody, seed phrase handling, private key handling, wallet file handling, or signing material handling.

## Render command

```bash
kubectl kustomize deploy/kubernetes/overlays/k3s
```

## Apply command

```bash
kubectl apply -k deploy/kubernetes/overlays/k3s
```

## Rollback notes

Use Git to revert overlay changes and `kubectl rollout undo deployment/bitcoin-bastion-api -n bitcoin-bastion-k3s` for deployment rollbacks. Validate database migrations and backups before rollback.

## Known limitations

- HPA is neutralized to one replica, not removed.
- No cloud load balancer is assumed.
- Local-path storage must be backed up by the operator.
- Recovery drills and heavy jobs may need manual scheduling or temporary suspension on weak hardware.
