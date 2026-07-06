# Frontend Security Review

The frontend must maintain the same security posture as the backend. It should never request, handle or transmit sensitive secrets such as Bitcoin seeds, private keys or raw Access Pass values.

## Key points

- **No custody flows** – The frontend does not custody funds. It must not implement transaction signing or broadcast flows.
- **No seed/private key handling** – Users must never paste a Bitcoin wallet seed or private key into the UI. The only seed handled is the Bastion Recovery Seed, which should be displayed once and stored offline by the user.
- **Proof‑of‑Access** – The frontend orchestrates the payment, certificate and session flow but does not implement authentication on its own. All premium requests must include the required Proof‑of‑Possession headers.
- **Secure storage** – Device keys should be generated and stored in secure contexts (OS keychain, WebCrypto in secure contexts). Raw session tokens and signatures must not be logged or stored.
- **Content security** – The frontend should enforce strict CSP and avoid dangerous HTML rendering. No untrusted HTML or markdown should be inserted into the DOM without sanitization.
- **Pending review** – Production security review is still pending full audit. Operators should treat the frontend as beta and review it before deployment.
