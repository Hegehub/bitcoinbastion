# PQ Issuer Chain Status

The Bastion issuer chain is currently **classical Ed25519** with truthful
post-quantum migration metadata. No ML-DSA, SLH-DSA, or ML-KEM provider is integrated.
The capability registry therefore reports every PQ signature suite as
`metadata_only`, with signing, verification and deterministic-vector status false.

Future hybrid activation requires a real provider, defined key generation/storage,
authoritative vectors, failure tests, client support, an explicitly activated crypto
epoch and object reissuance. Algorithm labels or environment flags cannot grant
hybrid, post-quantum, long-term-root, or Sovereign assurance.

Wallet control remains BIP-322/secp256k1 and Lightning control remains LNURL-auth/
secp256k1. PQ issuer protection applies to Bastion-issued authorization and evidence,
not to native wallet proofs or network consensus.
