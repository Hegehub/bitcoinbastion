# GitOps Structure

This repository uses a Kustomize-first layout with overlays for dev/staging/production.
ArgoCD application examples are included under `argocd/apps/`.
Promotion and rollback require operator approval and deployment evidence.
