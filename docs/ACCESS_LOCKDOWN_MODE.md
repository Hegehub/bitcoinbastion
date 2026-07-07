# Emergency Lockdown Mode

Emergency Lockdown Mode freezes compromised Bastion Proof-of-Access material quickly while preserving the recovery path. It is intended for suspected device compromise, child-key leakage, delegated-pass abuse, operator compromise, business workspace incidents, and enterprise emergency response.

## What lockdown freezes

For the current pass, lockdown freezes active sessions, revokes child API keys, revokes delegated passes, freezes linked devices where appropriate, and invalidates offline validity packs when that subsystem exists. Business and Enterprise scopes additionally freeze workspace/operator/device/bot artifacts according to policy.

## What lockdown does not delete

Lockdown never deletes audit history, payment records, certificate records, entitlement records, recovery quorum data, or incident evidence. It records revocation rows and a tamper-evident `access_lockdown_started` audit event.

## Recovery-only behavior

After lockdown, ordinary protected access must fail. Recovery/status endpoints remain available so the owner can complete recovery quorum and rotate compromised material. Disabling lockdown through an ordinary session is forbidden; release requires recovery quorum or high-assurance step-up.

## Support boundary

Support cannot unlock access alone. Support-only recovery, password fallback, bearer-token unlock, and Bitcoin seed/private-key input are prohibited.

## API example

```http
POST /api/v1/access/lockdown
```

```json
{
  "scope": "current_pass",
  "reason": "suspected_device_compromise",
  "confirmation_intent_signature": "...",
  "recovery_mode": true
}
```

Response:

```json
{
  "status": "locked_down",
  "lockdown_id": "lock_...",
  "affected_sessions": 3,
  "affected_child_api_keys": 2,
  "affected_delegated_passes": 1,
  "affected_devices": 1,
  "affected_offline_packs": 0,
  "recovery_only": true,
  "audit_event_hash": "sha256...",
  "created_at": "2026-07-05T00:00:00Z"
}
```

## Audit event example

The audit event stores only hashes/fingerprints and counts: `lockdown_id`, `actor_hash`, `pass_lookup_hash` or `workspace_id_hash`, `scope`, `reason_class`, affected counts, revocation epoch, policy decision id, and timestamp. It never includes raw Access Passes, raw session tokens, recovery phrases, private keys, Bitcoin seeds, or full raw device secrets.

## Operational runbook

1. Start lockdown from a valid Access session with Human Intent Signature, or from a verified recovery/emergency path.
2. Confirm affected counts and audit event hash.
3. Begin recovery quorum if the current device/session is compromised.
4. Rotate recovery material, device keys, child keys, delegated passes, and affected business/operator roles.
5. Do not disable lockdown until recovery quorum or high-assurance step-up succeeds.

Bastion will never ask for a Bitcoin seed or private key during lockdown or recovery.
