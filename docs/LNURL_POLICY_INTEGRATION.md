# LNURL Policy Integration

LNURL success does **not** equal policy allow. LNURL parsers and verifiers prove protocol facts; the central Proof-of-Access Policy Engine decides whether a verified actor may perform the requested operation.

## Protocol verification versus authorization

Protocol/verifier services remain responsible for LNURL decoding, k1 format validation, ECDSA signature verification, BOLT-11 parsing, invoice network checks, settlement provider reads, payerData parsing, successAction parsing, and comment parsing. `LNURLPolicyHooks` receives only verified status, hashes, fingerprints, normalized amounts, and state names, then calls the existing `AccessPolicyEngine`.

The hooks do not implement independent authorization logic, cryptographic verification, payment execution, or API routing.

## Supported actions

Stable LNURL policy actions include:

* LNURL-auth: `lnurl_auth_register`, `lnurl_auth_login`, `lnurl_auth_link`, `lnurl_auth_step_up`, `lnurl_auth_add_device`, `lnurl_auth_lockdown`, `lnurl_auth_recovery_factor`
* LNURL-pay: `lnurl_pay_create_request`, `lnurl_pay_issue_invoice`, `lnurl_pay_verify_settlement`, `lnurl_pay_create_payment_proof`, `lnurl_pay_issue_entitlement`, `lnurl_pay_upgrade_subscription`, `lnurl_pay_renew_subscription`
* Lightning Address: `lightning_address_resolve`, `lightning_address_create`, `lightning_address_update`, `lightning_address_disable`
* LNURL-withdraw: `lnurl_withdraw_create`, `lnurl_withdraw_accept_invoice`, `lnurl_withdraw_pay`, `lnurl_withdraw_cancel`, `lnurl_refund_create`, `lnurl_refund_pay`, `lnurl_partner_payout`, `lnurl_reward_payout`
* PayRegister: `payregister_lnurl_create_payment`, `payregister_lnurl_issue_invoice`, `payregister_lnurl_refund`, `payregister_lnurl_settlement`, `payregister_lnurl_terminal_enroll`
* Metadata/UX: `lnurl_payerdata_bind_auth`, `lnurl_success_action_create`, `lnurl_comment_store`

## Policy context fields

The normalized Access policy context carries actor type, principal hash/type, auth method(s), action, resource/object hash, request origin, auth domain, device fingerprint, session hash/status, subscription plan/status, scopes, metric group, business role, PayRegister store/terminal hashes, risk, verification strength, policy hash/epoch, revocation epoch/state, recovery state, step-up freshness, idempotency state, and audit requirement.

LNURL-specific context uses only safe fields: k1 hash/status/expiry/use time, linking-key hash, signature-verified flag, challenge/callback domains, domain-match flag, challenge action, internal action, wallet compatibility level, payment request hash/status, invoice hash/status, amount/expected amount, metadata/callback hashes, settlement status/method, payment proof hash, payerData flags, withdraw request/k1 hashes/status, invoice validity, payout policy/reference hashes, cooldown/quorum flags, Lightning Address hash/name/domain/status, product code, merchant hash, custom-domain status, and success/comment flags.

Raw k1, linking keys, signatures, invoices, preimages, wallet addresses, Access Passes, session tokens, private keys, seed phrases, and payer email are not policy context fields.

## Evaluation order

1. Normalize audit-safe LNURL context.
2. Resolve explicit actor and LNURL/internal action.
3. Attach revocation state from the configured revocation checker.
4. Attach verified protocol state.
5. Call the central Policy Engine.
6. Emit an audit-safe LNURL policy event.
7. Record low-cardinality metrics.
8. Return the structured decision.

Inside the Policy Engine, terminal denials for unknown actors, revoked principals, replayed/expired k1, invalid signature, expired session, or invalid payment/withdraw state are not overridden by later checks.

## Entitlement issuance protections

Entitlement issuance requires an active payment request, matching amount/product/plan, invoice ownership, settled invoice, verified settlement, valid payment proof, non-duplicate state, principal binding policy, active entitlement/subscription policy, clean revocation/fraud state, and an audit-required policy decision. Invoice issuance, client `paid=true`, successAction, comments, and unverified payerData cannot issue entitlements.

## Withdraw stages

LNURL-withdraw policy runs at three stages:

* Request creation before exposing a QR/LNURL: authenticated actor, PoP session, scope/role, purpose/reference, amount limit, cooldown, step-up, quorum, revocation, and risk.
* Invoice acceptance before accepting wallet BOLT-11: request active, withdraw k1 status, invoice validity, amount/network/expiry, recipient policy, and not already paid.
* Payment execution before paying: approval still valid, request/principal/workspace active, amount/cooldown/quorum still valid, no duplicate payout, and audit linkage.

## payerData, comments, and successAction

`payerData.auth` can be used only after cryptographic verification. Personal payerData fields are disabled by default and cannot grant permissions. Comments are untrusted metadata only; they cannot alter principal, plan, amount, scopes, role, device, entitlement, payout destination, or policy outcome. successAction is UX only; it cannot prove payment, issue entitlement, authorize login, complete recovery, or expose secret material.

## Audit, revocation, and observability

Every security-relevant hook emits an audit-safe policy event such as `lnurl_auth_policy_evaluated`, `lnurl_pay_entitlement_policy_evaluated`, `lnurl_withdraw_policy_evaluated`, `lightning_address_policy_evaluated`, `payer_data_policy_evaluated`, or `success_action_policy_evaluated`. Payloads include decision, reason code, actor type, principal/object hashes, action, risk, verification strength, policy hash/epoch, revocation epoch, and correlation ID only.

Hooks can call a configured revocation checker for principals, linking keys, k1 entries, devices, sessions, entitlements, payment requests/proofs, Lightning Addresses, merchants, PayRegister terminals, withdraw requests, recovery capsules, and Access Certificates. Metrics use low-cardinality labels only: action category, decision, reason category, actor type, verification strength, and environment.

## Fail-closed behavior

Policy Engine unavailability, malformed action mapping, unknown actor/action, ambiguous settlement or withdraw state, unavailable critical revocation checks, or policy epoch mismatch deny critical LNURL operations. A narrowly degraded public Lightning Address resolution mode may be configured separately, but there is no degraded mode for login session issuance, device binding, entitlement issuance, step-up, recovery, refunds, payouts, Business role changes, or PayRegister admin actions.

## Test coverage

Tests cover LNURL-auth allow/deny/replay/expiry/domain/signature/revocation/session/step-up cases, LNURL-pay settlement and duplicate-entitlement protection, Lightning Address policy control and non-authentication, staged withdraw controls, payerData/comment/successAction non-authorization, audit/metrics privacy, fail-closed behavior, and unknown actor/action denial.

## Wallet + LNURL step-up policy

Routine reads such as `read_basic_metrics`, `read_current_entitlements`, device listing, and watch-only wallet health use the active Device Binding and PoP Session; they do not require the wallet to sign every request.

High-risk actions such as `create_api_key`, `increase_scope`, `create_delegated_pass`, `add_device`, Business role binding, and PayRegister cashier pass creation require a structured Human Intent and either a fresh LNURL-auth `action=auth` proof or a fresh BIP-322 proof bound to the same intent hash and policy hash.

On-chain ownership-sensitive actions such as `treasury_policy_change` require fresh BIP-322 or stronger Bitcoin-wallet proof. LNURL-auth remains a domain-specific Lightning linking-key proof and is not treasury ownership proof.

Critical Business, Enterprise, recovery, payout, and lockdown actions may require hardware-wallet evidence, dual method, recovery quorum, multi-wallet quorum, or a sovereign ceremony. Client-provided strings claiming hardware-wallet use are ignored unless validated hardware evidence is bound to the same Human Intent hash.

Freshness defaults are 300 seconds for Human Intent, LNURL-auth step-up, BIP-322 step-up, hardware proof, and quorum windows. Fresh proof cannot upgrade a subscription plan, grant absent scopes, bypass metric/quota/object policy, or restore a revoked principal/device/session/factor.
