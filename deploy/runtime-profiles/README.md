# Runtime profile metadata

This directory stores machine-readable runtime profile metadata and operator guidance for Bitcoin Bastion deployment postures.

Runtime profiles describe how Bitcoin Bastion may be operated across Docker Compose, standard Kubernetes, K3s, Kind, Minikube, constrained single-node deployments, and bare-metal/systemd fallback deployments. The files in this directory are metadata and guidance; they are not secret stores and they are not full overlay implementations.

## Relationship to Kubernetes manifests

`deploy/kubernetes` is the canonical Kubernetes manifest path. Runtime profile metadata references that path for the standard Kubernetes profile and for planned Kubernetes-family profiles. This directory does not replace `deploy/kubernetes` and does not create a new canonical `k8s/` path.

Overlays for K3s, Kind, Minikube, and single-node Kubernetes are planned or added in separate profile-specific tasks. Until then, the corresponding profile files document posture, limitations, and future extension points only.

## Safety rule

Runtime profiles describe deployment posture. They do not authorize custody, signing, seed phrase storage, or private key handling.

Profiles do not contain secrets and do not imply custody. They preserve Bitcoin Bastion's no-custody model, operator control, explicit limitations, and evidence-driven release process.

## Runtime helper scripts

Use the runtime helper scripts for safe detection, dry-run rendering, validation, and explicit apply workflows:

```bash
python deploy/scripts/detect-runtime-profile.py
python deploy/scripts/render-runtime-profile.py --profile k3s --env staging --dry-run
./deploy/scripts/bastion-deploy detect
./deploy/scripts/bastion-deploy render --profile k3s --env staging
```

Dry-run is the default. Apply workflows require explicit `--apply --yes` and never generate secrets.
