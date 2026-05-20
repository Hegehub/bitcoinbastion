# Kubernetes Operator Runbook Lock

Lock date: 2026-05-20

## Locked operational command set (canonical)
1. `make k8s-render-dev`
2. `make k8s-render-staging`
3. `make k8s-render-production`
4. `make k8s-run-migration`
5. `make k8s-run-postgres-migration-smoke`
6. `make k8s-run-postgres-schema-parity`
7. `make k8s-run-release-evidence`
8. `make k8s-run-observability-validation`
9. `make k8s-run-evidence-archive`
10. `make k8s-status`

Any deviation requires incident/change record and post-action reconciliation.
