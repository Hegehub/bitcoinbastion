# Bastion Crypto Agility

The shared `BastionIssuerSignatureEnvelope` is the sole issuer metadata envelope for
Access, Wallet Auth, LNURL, Recovery, Offline Validity Pack, revocation, PayRegister,
policy and future transparency objects. Native Bitcoin and LNURL proofs remain
classical ecosystem proofs; the envelope authenticates Bastion-issued decisions and
does not alter Bitcoin or Lightning consensus.

> Post-quantum metadata does not by itself provide post-quantum security. Bastion
> grants post-quantum or hybrid assurance only after the required cryptographic
> signatures have been successfully created and verified by an operational
> implementation.

## Current state

Crypto epoch 1 is active. Ed25519 through `cryptography` is the only issuer algorithm
with operational sign-and-verify capability and deterministic tests. SHA-256 is the
canonical payload hash. ML-DSA and SLH-DSA variants are metadata-only: no provider,
key generation, private-key storage, signing or verification implementation exists.
ML-KEM values are declarations for future encrypted envelopes and are not active KEMs.
Setting `ACCESS_PQ_ENABLED=true` cannot change runtime capability and fails whenever
a PQ operation is required.

The default requirement is `classical_required_pq_optional`. An absent metadata-only
PQ signature does not invalidate a classical object. A supplied malformed PQ
signature fails; it is never ignored. `hybrid_required`, `pq_required` and
`long_term_root_required` fail closed in epoch 1. Planned epoch 2 declares a hybrid
migration target but is inactive and cannot activate silently.

## Envelope and migration

The version-1 envelope binds object type and fingerprints, canonicalization version,
explicit payload hash algorithm/value, issuer key ID/fingerprint/domain, crypto,
policy and schema epochs, validity, required signature policy, classical/PQ/root
slots, migration target and verification metadata. Contradictory states—such as PQ
assurance without a real PQ signature—are rejected at construction.

Existing Ed25519 signatures remain valid. Migrated records store the shared envelope
alongside legacy signatures; legacy rows are not rewritten or relabeled as PQ.
`verify_legacy_then_reissue` grants only classical assurance and marks reissuance.
Key rotation retains retired public keys for historical verification. Revoked or
compromised keys cannot sign and verification reports failure/reissuance requirements.
Private key bytes are resolved from configured providers at use time and are never
stored in application database records.

## Object coverage and limitations

Shared object typing covers Wallet/Lightning entitlements, Access Certificates,
delegated and child credentials, Recovery Capsules, Offline Validity Packs,
revocation/policy/transparency checkpoints, business/PayRegister credentials, LNURL
payment receipts, refunds, withdraw authorizations and merchant receipts. Raw LNURL
callbacks, payerData, comments, wallet addresses, linking keys, k1, seeds and private
keys are never credentials. Signed LNURL receipts authenticate Bastion evidence; they
do not replace settlement verification.

On issuer compromise, revoke/compromise the key in the key registry, activate
incident response, deny new signing, identify affected object fingerprints, mark
objects for reissue, rotate explicitly to a configured active epoch/key, and publish
the resulting audit/transparency evidence. Full transparency checkpoint behavior is
reserved for Prompt 63/72.
