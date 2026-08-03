# Frontend Security Review

No custody flows in frontend.
No seed/private key handling accepted.
No transaction signing/broadcasting.
No dangerous HTML rendering used in current baseline.
Production security review is partially complete and still pending full audit.

Security hardening baseline added; operations remain non-custodial and no signing/broadcasting.

## Access auth frontend security review

Frontend auth must not ask for an legacy credential login, Bitcoin seed, Bitcoin private key, xprv, WIF, wallet file, or raw Access Pass as a generic bearer credential. Browser UI is an interface, not the root of trust; production device signing should use Vault/device custody. Development signers must be disabled in production.

## Wallet/LNURL review

The browser is not presented as a root of trust. The centralized PoP transport accepts a non-exportable platform/device signer adapter and keeps session state in memory; frontend storage policy explicitly forbids raw wallet/LNURL signatures, Device private keys, Recovery Capsule material, raw Access Passes, and one-time child API keys. No localStorage/sessionStorage write path was added.

Authentication pages prominently state that Bastion never requests a Bitcoin seed/private key, authentication signatures do not authorize transactions, and a dedicated authentication wallet/address is recommended. QR images are generated locally with Segno and are never sent to an external QR service. LNURL callbacks remain backend-side, no CSP wildcard was added, and successAction navigation is never automatic.

This is not a production-readiness attestation. Real-wallet interoperability, a secure non-exportable browser Device signer integration, deployment capability flags, auth-attempt status polling, callback security, backend policy/revocation, and payment-provider settlement still require deployment validation.
