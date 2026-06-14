# Minikube local testing overlay

## Purpose

This overlay is for local Minikube testing only. It supports local operator testing, local ingress testing, developer demos, and single-machine Kubernetes experimentation against the canonical `deploy/kubernetes/base` manifests.

## Limitations

- It is not a production deployment profile.
- It does not prove production readiness.
- It does not include production TLS, CDN, WAF, HA, or disaster recovery evidence.
- It does not change Bitcoin Bastion's no-custody posture.
- Never provide seed phrases, private keys, wallet files, or signing material.

## Prerequisites

- Minikube installed and started locally.
- `kubectl` configured for the Minikube cluster.
- Local or mocked `bitcoin-bastion-secrets`; do not commit real credentials.

## Minikube ingress addon notes

Enable the Minikube ingress addon before applying the overlay if you want to test `Ingress/bitcoin-bastion` locally. The overlay uses the local hostname `bitcoin-bastion.minikube.local` and does not include production TLS, CDN, WAF, or public DNS assumptions.

```bash
minikube start
minikube addons enable ingress
```

## Render command

```bash
kubectl kustomize deploy/kubernetes/overlays/minikube
```

## Apply command

```bash
kubectl apply -k deploy/kubernetes/overlays/minikube
```

## Access command

```bash
kubectl -n bitcoin-bastion-minikube get pods,svc,ingress
minikube tunnel
```

## Evidence limitations

Minikube can validate local ingress behavior and operator workflows. It does not provide production readiness evidence, real TLS/WAF/CDN evidence, HA evidence, backup evidence, or disaster-recovery evidence.

## Production warning

This overlay is local-only. Do not use it for production or production-readiness claims.

## Cleanup command

```bash
kubectl delete namespace bitcoin-bastion-minikube
```
