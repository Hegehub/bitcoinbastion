# Wallet Auth Security

## Legacy Bitcoin Message Signature Compatibility

BIP-322 is the preferred Bitcoin wallet proof method for Bastion Wallet-first
Proof-of-Access Auth PQ v2. Legacy Bitcoin message signatures exist only as a
compatibility fallback for wallets that expose classic `signmessage` behavior but
not BIP-322.

Legacy signatures are disabled by default with:

```text
WALLET_AUTH_ALLOW_LEGACY_SIGNATURES=false
```

They run only when the caller explicitly requests
`proof_type=legacy_message_signature`; Bastion must not silently retry legacy
verification after a BIP-322 failure.

### Supported formats

The current verifier supports only legacy P2PKH address parsing and only when an
explicit recoverable secp256k1 backend is configured. The repository default
backend is conservative and returns unsupported rather than fabricating
cryptographic success.

### Unsupported formats

The legacy verifier does not claim support for Taproot, P2WSH, multisig,
descriptors, miniscript, P2SH, arbitrary scripts, or treasury descriptors. These
formats require BIP-322 or a stronger future proof path.

### Low-risk-only policy

Legacy signatures are compatibility-strength proof only. They may be considered
for Lite/Basic registration or login and limited existing-principal continuity
checks where policy allows. They are forbidden for high-risk actions including
API key creation, scope increases, delegated passes, treasury policy changes,
recovery completion, lockdown release, Business role assignment, Enterprise
policy changes, PayRegister administrator enablement, offline validity pack
issuance, Enterprise authentication, Sovereign mode, and high-assurance Access
Certificate issuance.

### Mandatory follow-up controls

A valid legacy signature is not authorization. Device Binding, a Proof-of-
Possession session, Subscription Entitlement checks, Revocation checks, and the
Policy Engine remain mandatory. A legacy wallet signature must never be reused as
an API request signature or bearer credential.

### Privacy and migration

Legacy verification must use privacy-preserving lookup hashes and proof
fingerprints rather than public `user_id` values. Raw signatures, raw addresses,
canonical intent payloads, seed phrases, private keys, mnemonics, xprv material,
Access Passes, and session tokens must not be logged. Users should migrate to
BIP-322 or LNURL-auth where supported.

## Lightning Principal Security

A Lightning Principal is a privacy-preserving cryptographic actor created only after an LNURL-auth callback proof has already been verified. It is not a legal identity, email account, username, password account, subscription entitlement, bearer token, Access Certificate, or proof of on-chain Bitcoin treasury ownership.

LNURL-auth linking keys are domain-specific. Bastion derives `lnurl_key_hash` with HMAC-SHA256 over the normalized auth domain and compressed linking public key, then derives `principal_hash` with a separate HMAC namespace for `lightning_wallet_principal`. Raw LNURL linking public keys are used only transiently at the verification boundary and must not become public user IDs.

Lightning Principals still require Device Binding, Proof-of-Possession session issuance, Subscription Entitlement checks where applicable, Revocation Registry checks, Audit Chain events, and Policy Engine authorization before protected API access. LNURL-auth success is not subscription payment, and an issued LNURL-pay invoice is not proof of settlement.

Domain migration is explicit. A principal created under `auth.bitcoin-bastion.com` must not silently authenticate as a principal for another domain. Bitcoin and Lightning principals are not automatically merged through payerData, payment correlation, Lightning Address use, IP address, or shared device context; linking requires explicit policy-approved proof and audit.

## LNURL-auth Audit Events

LNURL-auth challenge, callback, Lightning Principal, device-binding, session, and step-up transitions publish privacy-preserving security events into the existing Bastion Access Audit Chain. Each event records the transition type, outcome, safe principal/session/device/challenge hashes, policy and crypto epochs when available, and a stable reason code for denials or failures.

Audit records must never contain raw `k1`, DER signatures, raw LNURL linking keys, raw session tokens, Access Passes, private keys, wallet seeds, mnemonics, recovery material, payment preimages, or unrestricted payer data. The LNURL audit adapter rejects those fields before persistence and accepts only explicit hashes or fingerprints such as `challenge_hash`, `k1_hash`, `lnurl_key_hash`, `principal_hash`, `session_hash`, and `device_key_fingerprint`.

LNURL-auth audit events are canonicalized and hash-linked with `previous_event_hash` and `event_hash` through the shared tamper-evident audit chain. Duplicate retries reuse deterministic idempotency keys for the same semantic success transition; replay attempts are separate security events such as `lnurl_auth_replay_rejected` rather than duplicate successes. Security-critical transitions fail closed if audit persistence fails.
# Revocation extension

Wallet principals, proofs, devices, sessions, step-up proofs, recovery capsules and
quorum artifacts resolve through the authoritative Access Revocation Registry.
Principal full-tree revocation overrides fresh proof, new devices, certificates and
payments. Operational behavior and offline limitations are documented in
[`WALLET_LNURL_REVOCATION.md`](WALLET_LNURL_REVOCATION.md).

Wallet authentication security transitions are written through the canonical,
tamper-evident Access Audit Chain. Raw wallet/LNURL proof material is rejected before
persistence; see [`WALLET_LNURL_AUDIT_CHAIN.md`](WALLET_LNURL_AUDIT_CHAIN.md).
