# Offline Validity Packs

> Offline Validity Packs are constrained authorization snapshots. They are not
> bearer tokens, do not authorize Bitcoin transactions, and cannot replace online
> policy, revocation or recovery controls.

`OfflineValidityPackService` is the canonical v1 writer. Repository inspection found
existing action names, entitlement flags, signature context, revocation targets and
lockdown hooks, but no prior pack format or writer. The implementation therefore
extends those foundations rather than creating a competing legacy format.

## Format and bindings

The signed canonical JSON envelope is principal-bound, device-bound and entitlement-
bound. It includes a restrictive policy snapshot, optional Access Certificate
fingerprint, revocation/policy/crypto/entitlement epochs, validity and maximum-offline
windows, reconciliation deadline, queue limit, issuer key ID and a real Ed25519
signature. `post_quantum_signature` is `null`; no PQ implementation is claimed.
Pack expiry is bounded by profile, entitlement and certificate expiry. Scope and
metric snapshots are intersections and must be strict subsets of online authority.

The export filename should be `bastion-offline-validity-pack.bvp`. Importers must
limit input size, parse JSON as data only, verify fingerprint/signature/bindings/time/
epochs, reject unsupported extensions, and load it only into the local Vault. It
contains no raw Access Pass, session token, wallet address, LNURL key, private key,
seed, mnemonic, xprv or executable content.

## Profiles

* **read_only**: Basic or higher; cached metrics, reports, evidence and policy status;
  maximum four hours by default.
* **analyst_cached**: Plus or higher; cached analysis and local report generation;
  no fresh provider retrieval; maximum twelve hours.
* **payregister_cashier_shift**: Business or higher; Business certificate, step-up,
  cashier role/shift/store/terminal constraints and hard invoice/shift limits;
  maximum twelve hours.
* **business_degraded**: Business or higher; narrowly pre-approved continuity and
  read-only dashboards; certificate and step-up required.

Lite receives no private offline authorization. Enterprise and Sovereign operation
remains bounded and does not enable offline administration. Legacy Bitcoin message
proof is read-only compatibility evidence at most. LNURL-auth proves Lightning-key
continuity but never on-chain treasury ownership.

## Local policy, time and reconciliation

The local evaluator is not the online Policy Engine. It defaults to deny and can only
narrow the signed snapshot. Unknown actions and objects, treasury/administration,
recovery, lockdown release, role changes, transaction signing/broadcast and
LNURL-withdraw execution are denied. Counters bound operations, values and queued
events. A local append-only hash chain preserves event order; queue exhaustion freezes
privileged use.

Signed wall-clock bounds are combined with the last trusted online timestamp and a
monotonic/secure-clock integration boundary. Clock rollback is denied. If trusted
elapsed time is unavailable, privileged operation is denied; no hardware clock is
claimed by metadata alone.

Reconciliation verifies the local event chain and compares current pack, principal,
device, entitlement, revocation and policy state. It is idempotent by pack and chain
root. Policy changes or invalid event chains are preserved and reported rather than
retroactively represented as authorized. Emergency lockdown and parent revocation
revoke affected packs.

## PayRegister and LNURL limitations

Cashier mode may create a local invoice intent or receipt and queue an observation.
Invoice creation is not settlement. If local node/provider evidence is unavailable,
payment remains pending until reconciliation. payerData, comments, successAction and
Lightning Address metadata never grant authority. Cached LNURL-auth challenges are
not reusable, subscription entitlement cannot be minted from unverified payment, and
LNURL-withdraw payout execution is always online-policy gated.

Issuance is disabled by default with `OFFLINE_PACKS_ENABLED=false`. TTL, queue,
step-up, certificate, clock-tolerance and reconciliation settings are bounded in the
deployment configuration. Public endpoint wiring remains deferred until the Access
API can provide the complete online PoP, Human Intent and Policy Engine dependencies.
