# Frontend Wallet/LNURL QA Checklist

- [ ] `/access` offers Lightning and BIP-322 wallet proof without email/password fields.
- [ ] Mandatory seed/private-key, dedicated-auth-wallet, and non-transaction signature copy is visible.
- [ ] QR has accessible alt text, domain/action/expiry context, copy fallback, and mobile deep link.
- [ ] Expired challenges cannot be reused; missing auth-status API is shown as unavailable.
- [ ] Wallet/LNURL proof does not unlock protected data before Device Binding and PoP Session.
- [ ] Session expired/revoked/frozen/lockdown states have explicit recovery or re-authentication actions.
- [ ] Invoice-issued and payment-pending never display active entitlement.
- [ ] payerData personal fields are not auto-filled; comments remain bounded untrusted metadata.
- [ ] successAction URLs do not auto-open and are restricted to approved origins.
- [ ] Device revocation, step-up, Recovery Capsule, and Emergency Lockdown show backend policy requirements.
- [ ] No secret is written to localStorage/sessionStorage; one-time child keys are not retained.
- [ ] Keyboard, screen-reader, mobile, reduced-motion, and non-color status behavior are manually tested.
- [ ] Backend contract, callback security, real-wallet interoperability, and deployment flags are validated before production claims.
