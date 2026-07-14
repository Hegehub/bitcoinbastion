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
