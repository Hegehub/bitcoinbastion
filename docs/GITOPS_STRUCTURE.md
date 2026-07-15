# GitOps Structure

This repository uses a Kustomize-first layout with overlays for
development, staging, and production. Argo CD application examples and their
promotion policy are owned by `deploy/kubernetes/gitops/`; there is no
parallel root-level Argo CD tree. Promotion and rollback require operator
approval and deployment evidence.
