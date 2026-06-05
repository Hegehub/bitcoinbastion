# Runbook: Deployment, Migration and Evidence Failures

## Signals
- Startup reports migration mismatch.
- GitOps render or Argo CD sync fails.
- Evidence integrity checks fail.

## Actions
1. Halt rollout and preserve failed artifacts.
2. Compare rendered staging and production manifests.
3. Run migration smoke and schema parity checks.
4. Do not silently recover corrupted evidence; quarantine and record artifact references.
5. Store drill evidence with type `failed_deployment`, `failed_migration` or `evidence_integrity`.
