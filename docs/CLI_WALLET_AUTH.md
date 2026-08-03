# CLI Wallet-first Authentication

> **Bastion CLI will never ask for your Bitcoin wallet seed or private key.**

`bastion wallet-auth` implements an interface to the backend Wallet Auth architecture; it does not verify BIP-322 or create an alternate account system. The chain is external Bitcoin-wallet proof → Wallet Principal → Bastion Device Key binding → short-lived PoP Session → entitlement → Policy Engine. Wallet proof alone cannot authorize protected API calls.

## External signing

Run `wallet-auth challenge`, inspect the complete canonical intent, origin, network, expiry, device fingerprint, action, and safety warning, then sign in a compatible external wallet. Submit the public proof using `--proof-file`; `--signature` exists only for compatibility and warns about shell history. There are deliberately no seed, mnemonic, xprv, wallet-seed, Bitcoin-seed, or private-key options.

The Bastion Device Key signs API requests only and is not a Bitcoin key. `wallet-auth session` generates it with OS cryptographic randomness and sends only its public material/fingerprint. When `BB_CLI_VAULT_PASSPHRASE` is explicitly configured, the session and Device Key are stored in an AES-GCM encrypted file under the OS/XDG state directory, with directory mode `0700` and file mode `0600` on Unix. With no passphrase, state is not persisted. Bitcoin/Lightning wallet keys and raw recovery phrases are rejected.

Protected SDK calls use `Authorization: PoP` and canonical `Bastion-Request-*` headers. The shared Python SDK constructs the exact request digest and creates a fresh nonce/signature per request. Public commands remain public; the CLI never hardcodes plan permissions. Server decisions and exit behavior remain authoritative.

## Management

Use `me`, `entitlements`, `devices`, `device-revoke`, and `step-up` for safe principal/device operations. Recovery commands are Recovery Capsule interfaces; LNURL-auth can be one factor but is not locally deemed sufficient. `lockdown` explicitly confirms the freeze. `lockdown-release` delegates to high-assurance backend recovery and provides no force/bypass option.

JSON/YAML output passes through redaction. Session tokens, signatures, k1, Device private material, preimages, recovery material, Access Passes, and linking keys are never printed. Production readiness still depends on deployed backend proof verification, policy, revocation, recovery, audit, and wallet interoperability.
