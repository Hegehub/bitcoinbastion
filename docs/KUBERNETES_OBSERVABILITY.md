# Kubernetes Observability

This package adds production observability artifacts under `deploy/kubernetes/observability`:
- Dashboard set (overview/runtime/provider/citadel/workers/release evidence)
- Rule packs for SLO/runtime/provider/citadel/workers/evidence-jobs
- Alertmanager routing + receivers examples
- Incident automation webhook example
- Validation job and fatigue control notes

Important: internal operational SLOs are not public SLA and do not imply attained production SLO without burn-in evidence.
