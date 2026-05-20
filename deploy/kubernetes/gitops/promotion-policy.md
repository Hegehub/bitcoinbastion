# Promotion policy
## Dev -> Staging gates
- lint/tests pass
- kustomize render pass
- image built and digest recorded
- no unapproved CRITICAL vulnerabilities

## Staging -> Production gates
- staging deploy succeeded
- migration/smoke/schema parity/release evidence jobs succeeded
- observability validation succeeded
- health/readiness passed
- provider posture acceptable or explicitly acknowledged
- Citadel synthetic and protocol advisory limitations acknowledged
- operator approval recorded
