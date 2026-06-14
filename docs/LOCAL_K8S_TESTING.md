# Local Kubernetes Testing

Bitcoin Bastion includes local-only Kubernetes overlays for Kind and Minikube under the canonical Kubernetes path, `deploy/kubernetes`. These overlays are for developer/operator testing and manifest validation only. Kubernetes remains optional for Bitcoin Bastion, and these local overlays do not replace Docker Compose or production-oriented Kubernetes overlays.

## Production warning

Kind and Minikube overlays are not production deployment profiles. They do not prove production readiness, do not provide production TLS/CDN/WAF evidence, do not provide HA, and do not provide disaster-recovery evidence. Production readiness still requires environment-specific evidence artifacts, monitoring validation, backup/restore evidence, secrets handling validation, ingress/TLS validation, and operational drills.

These overlays do not change Bitcoin Bastion's no-custody posture. Never provide seed phrases, private keys, wallet files, or signing material.

## Kind workflow

Kind is for local manifest validation, CI-like local Kubernetes testing, and developer smoke tests.

```bash
kubectl kustomize deploy/kubernetes/overlays/kind
kubectl apply -k deploy/kubernetes/overlays/kind
kubectl -n bitcoin-bastion-kind get pods,svc,ingress
kubectl -n bitcoin-bastion-kind port-forward svc/bitcoin-bastion-api 8000:8000
kubectl delete namespace bitcoin-bastion-kind
```

The Kind overlay patches the API service to `NodePort` for local workflows, but port-forwarding is the safest default unless your Kind cluster explicitly maps node ports.

## Minikube workflow

Minikube is for local operator testing, local ingress experiments, and developer demos.

```bash
minikube start
minikube addons enable ingress
kubectl kustomize deploy/kubernetes/overlays/minikube
kubectl apply -k deploy/kubernetes/overlays/minikube
kubectl -n bitcoin-bastion-minikube get pods,svc,ingress
minikube tunnel
kubectl delete namespace bitcoin-bastion-minikube
```

The Minikube overlay uses `bitcoin-bastion.minikube.local` as a local hostname example. Configure your local hosts/DNS as needed. Do not commit real domains, credentials, or TLS secrets.

## Render-only validation

`kubectl kustomize` validates that manifests render locally. Rendered manifests are useful for smoke checks and review, but rendered manifests are not production evidence by themselves.

## Apply/delete lifecycle

Apply local overlays only to local Kind or Minikube clusters. Delete the local namespace when testing is complete to avoid stale resources and misleading evidence.

## Port-forward notes

Use `kubectl port-forward` for local API access when ingress or NodePort behavior is not configured. This avoids implying public production ingress readiness.

## Ingress notes

Minikube ingress tests require `minikube addons enable ingress`. Kind ingress varies by cluster setup and is not assumed by the Kind overlay.

## Known limitations

- Local clusters are not HA.
- Local clusters do not prove production readiness.
- Local render/apply success does not prove production TLS, WAF, CDN, backup, restore, monitoring, alerting, or disaster recovery.
- Local secrets should be mocks or development-only values.
