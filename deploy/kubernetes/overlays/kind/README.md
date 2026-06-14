# Kind local testing overlay

## Purpose

This overlay is for local Kubernetes testing only. It supports local manifest rendering, CI-like local Kubernetes smoke testing, and developer validation against the canonical `deploy/kubernetes/base` manifests.

## Limitations

- It is not a production deployment profile.
- It does not prove production readiness.
- Rendered manifests are local validation artifacts, not production evidence.
- It does not include production TLS, CDN, WAF, HA, disaster recovery, or backup evidence.
- It does not change Bitcoin Bastion's no-custody posture.
- Never provide seed phrases, private keys, wallet files, or signing material.

## Prerequisites

- Kind cluster running locally.
- `kubectl` configured for the Kind cluster.
- Local or mocked `bitcoin-bastion-secrets`; do not commit real credentials.

## Render command

```bash
kubectl kustomize deploy/kubernetes/overlays/kind
```

## Apply command

```bash
kubectl apply -k deploy/kubernetes/overlays/kind
```

## Port-forward / NodePort access notes

The overlay patches `Service/bitcoin-bastion-api` to `NodePort` on port `30080` for local access where Kind node port mapping is configured. Port-forwarding is the safest default workflow:

```bash
kubectl -n bitcoin-bastion-kind get pods,svc,ingress
kubectl -n bitcoin-bastion-kind port-forward svc/bitcoin-bastion-api 8000:8000
```

## Evidence limitations

Kind can validate manifest shape and basic local smoke workflows. It does not provide production readiness evidence, runtime SLO evidence, real ingress/TLS evidence, or disaster-recovery evidence.

## Production warning

This overlay is local-only. Do not use it for production or production-readiness claims.

## Cleanup command

```bash
kubectl delete namespace bitcoin-bastion-kind
```
