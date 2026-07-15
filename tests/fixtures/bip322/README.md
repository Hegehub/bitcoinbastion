# BIP-322 test fixtures

These fixtures are vendored for offline CI. CI must not download BIP-322
fixtures from the internet.

- Source: official Bitcoin BIPs repository, BIP-0322 Generic Signed Message Format.
- Upstream path: `bip-0322.mediawiki` in the Bitcoin BIPs repository.
- BIP number: BIP-0322.
- Captured specification version/date: 2026-07-12 repository target date.
- License: Bitcoin BIPs repository license for specification/test-vector material.
- Retrieval date: 2026-07-12.

Files:

- `basic-test-vectors.json`
  - SHA-256: `a925c615e0d74f4406ec397f13cccf4ce5d95eacb80f29f3bae3ca6d8a4902ec`
  - Use: message-tagged-hash cases for empty, `Hello World`, and UTF-8 payloads.
- `generated-test-vectors.json`
  - SHA-256: `2b0c1246deefa7fd46fbb6da565e1785bcac49ec2989b8a52d83d9afa9d2db20`
  - Use: deterministic Bastion structural vectors for witness-stack parsing and virtual transaction construction.

The current production verifier includes strict BIP-322 parsing, message hashing,
address/network/script derivation, and deterministic virtual transaction
construction. Cryptographic script execution is behind a narrow backend protocol.
Until a trusted script backend is integrated, script-valid vectors are exercised
with explicit test backends only, and the default backend returns `inconclusive`
rather than fabricating success.
