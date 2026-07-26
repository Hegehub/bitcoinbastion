# Wallet/LNURL revocation runbook

## Common prerequisites and verification

Authenticate with the administrative/self-service scope required by policy, obtain
fresh Human Intent step-up for critical changes, identify only safe hashes, and
record the incident correlation ID. Submit the target, structured reason and scope
to the Access Revocation Registry. Verify the Policy Engine returns `revoked`, the
expected audit event exists, propagation is complete, and low-cardinality revocation
metrics increased. Reversal is append-only and never restores old sessions.

| Incident | Registry action | Expected effect/event | Escalate when |
|---|---|---|---|
| Compromised principal | Revoke wallet principal with `actor_full_tree` | Sessions, devices, children, certificates and packs denied; `wallet_principal_revoked` | Any descendant remains usable |
| Lost device | Revoke `wallet_device` with `device_lost` | Device sessions/step-up invalid; `wallet_device_revoked` | Re-enrollment appears without fresh proof |
| Compromised LNURL key | Revoke `lnurl_auth_key`, domain/product scope as applicable | Login and payerData binding denied; `lnurl_auth_key_revoked` | Key authenticates on any intended alias |
| K1 replay | Preserve K1 evidence and mark replay detected | Callback denied; `lnurl_k1_replay_detected` and replay metric | Concurrent callbacks both succeed |
| Payment proof dispute | Revoke `lnurl_payment_proof` | Entitlement enters denial/review; proof history retained | Existing consumed service is rewritten |
| Disable address | Revoke `lightning_address` or terminal alias | New routing/invoices stop; historic receipts remain | Store-wide routing stops unintentionally |
| Cancel withdraw/refund | Revoke request before payout authorization commit | Callback/invoice/payout denied; request event emitted | Payment was already sent (incident/reconciliation) |
| Decommission terminal | Revoke terminal and its pack/routes | Terminal denied; store address remains | Scope propagates beyond terminal |
| Workspace lockdown | Apply `emergency_lockdown` to workspace | Roles, shifts, devices, payouts and packs freeze | Any critical workspace action succeeds |
| Rotate recovery capsule | Revoke old capsule/quorum attempt, create new commitment | Old capsule cannot count; recovery audit emitted | Old commitment remains usable |

For a mistaken revocation, append a reversal after high-assurance policy approval,
then require every actor/device to authenticate into a **new** session. Check offline
packs still in circulation against their expiry and shift boundary; do not claim
instant invalidation while a terminal is disconnected.

