# Wallet + LNURL Policy Actors

Bastion authorization is explicit and typed: a verified actor plus verified authentication methods, active device binding, PoP session, subscription entitlement, scopes, metric entitlements, quota, resource policy, risk, revocation, optional step-up, optional quorum, and optional Access Certificate produces a policy decision.

## Actor types

* `bitcoin_wallet_principal` — BIP-322, hardware, air-gapped, quorum, or limited legacy Bitcoin message proof. This may prove control of a hashed on-chain wallet identifier, but never automatically grants treasury permissions.
* `lightning_wallet_principal` — LNURL-auth domain-specific linking-key proof. It is usable for registration, login, linking, device binding, PoP session issuance, subscription activation after settled payment, standard API access through PoP, step-up, PayRegister roles, and configured recovery factor use. It is not on-chain treasury proof, legal identity, global identity, a Lightning Address identity, or full authorization by itself.
* `wallet_device` — bound local device public key used for continuity, PoP sessions, request signing, risk, and trusted-device decisions. It is not the wallet private key.
* `access_certificate` — Bastion-issued high-assurance credential. It is optional evidence and is not bearer access.
* `child_api_key`, `delegated_pass`, `bot` — scoped child or delegated actors constrained by parent status, parent scopes, expiry, resources, depth, and cannot-access restrictions.
* `business_role` — effective role binding evaluated separately from the authenticated principal.
* `payregister_device` — merchant/workspace-bound, device-bound, role-bound terminal actor.
* `service_account` — explicit internal machine identity with explicit scopes; never accepted as wallet principal.
* `recovery_actor` — temporary recovery-only actor with no normal API access.

## Authentication methods

Stable methods are: `bip322`, `legacy_bitcoin_message`, `hardware_wallet`, `air_gapped_wallet`, `multi_wallet_quorum`, `lnurl_auth`, `access_certificate`, `device_pop`, `session_pop`, `child_api_key`, `delegated_pass`, `recovery_capsule`, and `internal_service_identity`.

Actor type and authentication method are separate. A Lightning Principal continuing through a device PoP session uses `actor_type=lightning_wallet_principal` with `lnurl_auth`, `device_pop`, and `session_pop` methods.

## Assurance levels

* `compatibility` — legacy or partial compatibility; low-risk only.
* `standard` — valid BIP-322 or LNURL-auth with replay protection plus active device/session evidence.
* `high_assurance` — verified hardware, fresh step-up, Access Certificate, or dual evidence where configured.
* `sovereign` — quorum, air-gapped approval, Access Vault, transparency checkpoint, or sovereign profile evidence.

Proof type alone does not assign high or sovereign assurance. Critical actions reject compatibility proofs.

## Risk, step-up, quorum, and resource rules

Low-risk reads usually require an active standard session. Medium-risk API use requires principal proof, bound device, PoP session, active entitlement, and normal policy approval. High-risk actions such as adding devices, creating API keys, delegated passes, valuable withdraw requests, or Business operator/cashier assignment require fresh step-up and Human Intent where configured. Critical actions such as recovery completion, treasury policy change, Enterprise policy change, owner transfer, high-value payout/refund, or disabling controls require high assurance or sovereign quorum and auditable policy approval.

Business roles are composed from principal identity, workspace binding, role binding, device binding, and shift binding. Cashiers can create configured payment requests and limited refunds but cannot administer Business, treasury, entitlement, or owner policy. Admins cannot replace owners without configured proof or quorum.

PayRegister devices can create payment intents, resolve configured Lightning Addresses, create LNURL-pay requests, generate receipts, request approved refunds, and use limited offline packs. They cannot transfer owners, change Business/treasury/security policy, complete recovery, or execute unrestricted payouts.

## LNURL-specific constraints

LNURL-auth requires expected single-use k1, valid signature, matching action/domain, unexpired challenge, and clean replay registry. LNURL-pay creates entitlements only after invoice existence, settlement, verification, payment proof, amount/product/plan match, and duplicate-entitlement checks. Lightning Address resolution is payment routing only. Payer data and comments are untrusted and never grant authorization.

## Privacy constraints

Policy context and decision output use hashes and fingerprints only. They must not include raw Bitcoin addresses, LNURL linking keys, k1 values, signatures, session tokens, raw Access Passes, recovery material, private keys, or seed phrases.

## Example decisions

```json
{
  "decision": "allow",
  "actor_type": "lightning_wallet_principal",
  "auth_methods_used": ["lnurl_auth", "device_pop", "session_pop"],
  "authentication_assurance": "standard",
  "requested_action": "read_metric",
  "requested_scope": "signals:standard:read",
  "requires_step_up": false,
  "requires_quorum": false,
  "audit_required": true
}
```

```json
{
  "decision": "step_up_required",
  "reason_code": "fresh_lnurl_auth_required",
  "actor_type": "lightning_wallet_principal",
  "requested_action": "create_api_key",
  "required_step_up_methods": ["fresh_lnurl_auth", "human_intent", "session_pop"],
  "audit_required": true
}
```

```json
{
  "decision": "deny",
  "reason_code": "lightning_principal_not_treasury_proof",
  "actor_type": "lightning_wallet_principal",
  "requested_action": "treasury_policy_change",
  "required_step_up_methods": ["bip322_or_hardware_wallet", "human_intent", "session_pop"],
  "audit_required": true
}
```

```json
{
  "decision": "quorum_required",
  "reason_code": "quorum_required",
  "actor_type": "bitcoin_wallet_principal",
  "requested_action": "enterprise_policy_change",
  "required_quorum": "2-of-3",
  "authentication_assurance": "sovereign",
  "audit_required": true
}
```
