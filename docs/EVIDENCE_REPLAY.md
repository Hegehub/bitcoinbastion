# Evidence Replay

Evidence Replay is the production replay subsystem for Bastion Market Time Machine evidence. It is designed around:

```text
Evidence over claims.
Replay over trust.
Traceability over assumptions.
```

## Replay capabilities

`EvidenceReplayService` supports:

- `replay_article()`
- `replay_event()`
- `replay_impact()`
- `replay_attribution()`
- `replay_signal()`
- `replay_publication()`

Replay output includes input entities, derived entities, hashes, scores, confidence provenance, policy adjustments, review decisions, limitations, evidence timeline, evidence chain, integrity status, operator review status, and publication status.

## Timeline

Replay timelines use timestamped production steps when data is available:

```text
Article fetched
  ↓
Event clustered
  ↓
Impact calculated
  ↓
Attribution created
  ↓
Signal candidate created
  ↓
Policy evaluated
  ↓
Operator reviewed
  ↓
Published
```

## Integrity

Integrity snapshots use deterministic SHA-256 hashing over selected public evidence fields. Secrets are not hashed; secret-like fields are redacted before hashing. Integrity checks compare the latest snapshot with the current entity hash and expose mismatches instead of hiding them.

## Failure behavior

Replay failures are written to `evidence_replay_logs` with input/output hashes where available, success status, error code, and metadata. Failures remain visible in API responses.

## Safety

Replay is correlation-based evidence, not proof of causation. It is not financial advice and does not make trading recommendations.
