# Wallet and LNURL revocation

Bastion uses the existing Access Revocation Registry as the authoritative source
for Access Certificates, wallet actors, LNURL objects, Business objects and
PayRegister objects. Protocol success, a fresh wallet proof, a settled payment,
or a newly enrolled device cannot override a principal revocation.

## Targets, scope and inheritance

Stable targets cover wallet principals/proofs/devices/sessions/step-up proofs,
LNURL auth keys/challenges/k1/pay requests/payment proofs/withdraw requests and
Lightning Addresses, recovery/quorum artifacts, entitlements/certificates/offline
packs, workspaces/roles/shifts and PayRegister terminals. Lookup identifiers that
derive from private values use HMAC-SHA256 with `ACCESS_REVOCATION_PEPPER`; raw
addresses, keys, k1 values, invoices, signatures and tokens are not registry data.

Scopes are `object_only`, `actor_and_sessions`, `actor_and_devices`,
`actor_and_children`, `actor_full_tree`, `product_only`, `workspace_only`,
`domain_only`, `global`, and `emergency_lockdown`. Parent resolution is bounded:
an actor full-tree revocation synchronously denies descendants even while explicit
child propagation is pending. Product/domain/global revocation must use only
correlation that already exists; the implementation must report partial propagation
rather than invent cross-product identity.

Revocations are append-oriented. A reversal appends a marker and requires new
authentication; it does not reactivate old sessions, challenges, or step-up proofs.
Temporary suspensions expire at their explicit expiry. Payment and audit history is
never deleted or rewritten.

## LNURL behavior

The existing transactional K1 Registry owns issuance and atomic single-use
consumption. The LNURL revocation adapter checks the Access registry first and
records confirmed replay as a revocation/audit event. Used, expired, revoked, and
replayed k1 values never become valid again. Raw k1 is never audited.

Revoking a pay request stops new invoices and entitlement issuance but does not
rewrite a settled payment. Invalidating a payment proof causes Policy review or
denial without automatically revoking its principal. Revoking a Lightning Address
stops routing, not identity. Revoking a withdraw request prevents invoice acceptance
and payout; an already irreversible payout remains factual and requires incident
reconciliation.

## Offline and distributed operation

Offline packs embed revocation epoch, policy epoch, entitlement expiry and a bounded
maximum offline age. Epoch mismatch requires an online check, and critical/admin or
treasury operations are never approved offline. **A fully disconnected device
cannot be revoked instantly.** Its residual access lasts at most the pack's bounded
validity/shift window; emergency procedures must account for devices still offline.

The database is authoritative. Cache entries must include the revocation epoch and
have short TTLs. Critical checks fail closed if authoritative state is unavailable.
Direct indexed target and parent checks occur before bounded propagation; no request
path scans audit history or traverses an unbounded graph.

