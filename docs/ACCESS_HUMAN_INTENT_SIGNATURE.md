# Access Human Intent Signature

Bitcoin Bastion uses Human Intent Signature for critical Proof-of-Access actions. A random challenge proves a device can sign bytes; it does **not** prove the human saw and approved the exact action. Human Intent Signature requires the user to sign a canonical, human-readable manifest describing the action, scopes, denied capabilities, target resource, origin, consequences, policy decision reference, and expiry.

## Critical actions

Human Intent is required for API key creation, scope increases, data export, delegated pass creation, PayRegister admin enablement, treasury policy changes, recovery changes, device add, lockdown disable, business role assignment, enterprise policy changes, subscription upgrades with new permissions, offline validity packs, recovery seed rotation, issuer-bound device rotation, step-up disablement, operator/cashier/bot pass creation, metric quota increases, and enterprise private policy enablement.

## Manifest structure

The manifest is a canonical JSON object with `type=bastion_human_intent`, version, action, actor/device fingerprint, certificate fingerprint, session fingerprint, origin, requested/granted scopes, explicit `cannot_access`, target resource hash, plan code, risk level, expiry, nonce, human summary, consequences, policy decision reference, and request hash.

`canonical_manifest_hash = SHA256(canonical_json(manifest))` using the Access hashing canonicalization rules. Device/Vault software must display `human_summary`, `consequences`, requested scopes, `cannot_access`, risk level, origin, and target before signing.

## Verification and audit

The service verifies the bound device signature over the canonical manifest hash with the Access signature suite. Verified intents are single-use: once consumed, replay fails. Tampering with action, origin, scope, `cannot_access`, target, expiry, nonce, or summary changes the hash and invalidates the signature.

Audit events record only intent hashes, actions, fingerprints, target hashes, risk levels, decisions, and reasons. Raw signatures, Access Passes, session tokens, recovery phrases, private keys, Bitcoin seeds, and wallet private keys must never be logged or stored.

## Safety rule

Bastion Human Intent Signature never asks for a Bitcoin seed or private key. Never enter a Bitcoin wallet seed into Bastion.
