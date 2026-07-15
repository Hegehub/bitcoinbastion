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
