# Wallet BIP-322 Verifier

## Specification target

The verifier targets the completed BIP-322 Generic Signed Message Format for
Bastion Wallet-first Proof-of-Access Auth PQ v2 planning and implementation.
It implements deterministic BIP-322 message tagged hashing, strict variant
parsing, strict Base64 decoding, SegWit address/network/script derivation, and
BIP-322 virtual transaction construction.

Required warning: A valid BIP-322 proof demonstrates that the submitted proof
satisfies the claimed Bitcoin script for the signed message. It does not prove
personal identity, current wallet balance, ownership of all funds associated
with a person, or that the signer sent a previous transaction.

Bitcoin Bastion will never ask for a Bitcoin seed phrase or private key.

## Supported signature variants

- `smp`: parsed as the simple witness-stack proof variant.
- `ful`: parsed and routed to the backend boundary; currently inconclusive with
  the conservative default backend.
- `pof`: parsed and rejected for authentication by default with
  `proof_of_funds_not_allowed_for_auth`.

Prefixless BIP-322 simple signatures are disabled by default. They can be parsed
only when `BIP322VerifierConfig.allow_prefixless_simple=True`, in which case the
result carries the `prefixless_compatibility_mode` limitation and must not be
used for sovereign policy.

## Script types

Fully verified by default backend: none. This is intentional fail-closed
behavior because the repository currently has no full Bitcoin script interpreter
or secp256k1/Schnorr backend dependency beyond general `cryptography`.

Parsed and dispatched:

- P2WPKH: decoded and routed to the backend.
- P2TR key-path: decoded and routed to the backend; Taproot script-path witness
  shapes return inconclusive with `unsupported_taproot_script_path`.
- P2WSH: decoded and routed to the backend; the conservative default backend
  returns inconclusive with `script_backend_unavailable`.

Unsupported or malformed scripts fail closed as invalid or inconclusive. The
verifier never treats public-key presence in a witness as proof of control.

## Selected backend

The selected production default is `ConservativeBIP322ScriptBackend`. It is a
narrow, replaceable script-verification backend that never returns success unless
a future trusted backend validates the relevant script conditions.

This avoids unsafe shortcuts such as legacy `verifymessage`, public-key-only
checks, heuristic multisig counting, explorer lookups, or remote verification
services.

## Valid, invalid, and inconclusive

- `valid`: a trusted backend completed script validation for the exact canonical
  structured Bastion Auth Intent and claimed script.
- `invalid`: a definitive check failed, such as malformed Base64, invalid
  prefix, malformed address, wrong network, empty witness, or invalid signature.
- `inconclusive`: the verifier cannot safely evaluate the script, such as when a
  trusted script backend is unavailable or the proof uses unsupported full/P2WSH
  semantics.

Policy must treat `inconclusive` as denied unless a separate safer verification
path succeeds.

## Network handling

The verifier supports `bitcoin-mainnet`, `bitcoin-testnet`, `bitcoin-signet`,
and `bitcoin-regtest` domain values. Address HRP and expected network must
match. Mainnet proofs do not satisfy testnet/signet/regtest challenges. Regtest
must remain disabled by production policy outside explicit development contexts.

## Input limits

Default limits are centralized in verifier constants/configuration:

- message bytes: 8192
- signature bytes: 131072
- witness items: 128
- witness item bytes: 65536
- virtual transaction bytes: 131072
- full variant parsing: enabled but conservative backend returns inconclusive
- proof-of-funds: disabled for authentication
- prefixless simple: disabled by default

Oversized input is rejected before expensive verification work.

## Privacy and logging

The verifier must not log raw BIP-322 signatures, witness stacks, wallet
addresses, structured intents, raw nonces, seed phrases, private keys, xprv
material, Access Passes, session tokens, or recovery material. Safe outputs use
wallet lookup hashes, proof fingerprints, scriptPubKey commitments, variant,
script type, outcome, and stable reason codes.

## No-custody and no-authorization boundary

The verifier does not sign messages, broadcast transactions, fetch balances,
query block explorers, create Wallet Principals, bind devices, issue PoP
sessions, issue entitlements, or make Policy Engine authorization decisions.
