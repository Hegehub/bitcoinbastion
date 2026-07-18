# Wallet-first Authentication Notes

Wallet-first authentication models cryptographic actors rather than classic email/password users.

## Lightning Principals

A Lightning Principal represents control of a domain-specific LNURL-auth linking key. It does not represent legal identity, global identity, on-chain Bitcoin ownership, subscription entitlement, or authorization for protected API actions.

Bastion stores privacy-preserving identifiers only:

- `lnurl_key_hash`: HMAC-SHA256 over normalized auth domain and compressed LNURL linking public key.
- `principal_hash`: HMAC-SHA256 over the Lightning principal actor type, auth domain, and `lnurl_key_hash`.
- optional product pseudonyms derived from product-specific HMAC namespaces.

No global `user_id`, mandatory email, username, password, wallet seed, mnemonic, xprv, raw k1, raw LNURL signature, or linking private key is introduced for Lightning Principals.

## Access Boundary

After LNURL-auth verification, the Lightning Principal service can create or locate a principal and return a safe authentication context for later services. It does not issue a Proof-of-Possession session, activate a subscription, issue an Access Certificate, or authorize protected API access.

Device Binding, PoP Session, Subscription Entitlement, Revocation Registry, Audit Chain, and Policy Engine checks remain mandatory. BIP-322 or another Bitcoin wallet proof is still required when an operation needs proof of on-chain Bitcoin wallet control.

## Linking

Bitcoin and Lightning principals may be linked only through explicit policy-approved flows with fresh proof and audit. Bastion must not infer identity linkage from payment correlation, payerData, Lightning Address routing metadata, shared IP address, or shared device context.

## LNURL successAction boundary

LNURL `successAction` is post-payment presentation metadata. It does not authenticate a wallet principal, does not create a PoP session, and does not authorize protected API access. Opening an activation or receipt URL only displays server-side state; subscription access still requires verified settlement, a Bastion Payment Proof, wallet or Lightning principal binding, signed Subscription Entitlement, revocation checks, and Policy Engine approval.
