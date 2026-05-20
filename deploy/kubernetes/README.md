# Kubernetes Production Foundation

This directory provides a production-oriented Kubernetes baseline for Bitcoin Bastion.

## Important constraints
- These manifests are a **foundation**, not proof of production readiness by themselves.
- No real credentials are committed.
- Keep no-custody posture: do not add seed/private-key handling.

## Structure
- `base/`: shared manifests for namespace, workloads, networking, and monitoring.
- `overlays/staging`: staging environment patch set.
- `overlays/production`: production environment patch set.

## Required secrets
Create `bitcoin-bastion-secrets` from your secret manager (or External Secrets later), with:
- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET_KEY`
- `TELEGRAM_BOT_TOKEN`
- `BOT_API_BEARER_TOKEN`
- `BITCOIN_ESPLORA_URL` (if your deployment uses it)

Use `base/secret.example.yaml` only as a template.

## Render and apply
```bash
make k8s-render-staging
make k8s-render-production
make k8s-apply-staging
make k8s-apply-production
make k8s-status
```

## External Secrets migration path
Current baseline uses native Secret references for compatibility. To adopt External Secrets later:
1. Replace manually managed `bitcoin-bastion-secrets` with `ExternalSecret`.
2. Keep env key names unchanged.
3. Remove direct Secret creation from operator workflows.
