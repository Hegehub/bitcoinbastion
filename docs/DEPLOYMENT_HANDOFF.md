# Deployment Handoff

- Validate required env vars (`docs/ENVIRONMENT_VARIABLES.md`)
- Use GitOps overlays and external secret management
- Ensure observability stack and alerting are configured
- Validate rollback path before promotion
- Promote from staging only after evidence gates pass
