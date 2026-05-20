# GitOps release governance

- Uses app-of-apps + project + environment apps (dev/staging/production).
- Dev/staging can autosync; production is manual-sync by default.
- Promotions are digest-based and evidence-gated.
- Rollback is Git revert + Argo sync.
- Emergency override is break-glass only and must be reconciled back to Git.
