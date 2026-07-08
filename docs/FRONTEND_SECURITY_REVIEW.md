# Frontend Security Review

No custody flows in frontend.
No seed/private key handling accepted.
No transaction signing/broadcasting.
No dangerous HTML rendering used in current baseline.
Production security review is partially complete and still pending full audit.

Security hardening baseline added; operations remain non-custodial and no signing/broadcasting.

## Access auth frontend security review

Frontend auth must not ask for an legacy credential login, Bitcoin seed, Bitcoin private key, xprv, WIF, wallet file, or raw Access Pass as a generic bearer credential. Browser UI is an interface, not the root of trust; production device signing should use Vault/device custody. Development signers must be disabled in production.
