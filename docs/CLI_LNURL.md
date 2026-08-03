# CLI LNURL Layer

`bastion lnurl` orchestrates backend-owned LNURL-auth, LNURL-pay, verification, Lightning Address discovery, and policy-gated withdraw. It never verifies linking-key signatures locally and never derives a linking key from a Lightning seed.

## Auth

`lnurl auth`, `auth-login`, and `auth-register` request a backend-generated single-use challenge and display the LNURL URI, expected auth domain, action, expiry, and pending state. k1 is not separately cached or displayed. The Lightning wallet calls Bastion directly. LNURL-auth proves domain-specific Lightning-wallet control; protected APIs still require Device Binding and a PoP Session. `auth-step-up` is explicit and action-bound.

No QR dependency is installed. `--qr` safely falls back to the URI; QR data contains only the public LNURL challenge. Internet domains require the backend/SDK HTTPS policy; Onion operation requires explicitly configured Tor transport and does not disable TLS globally.

## Pay and addresses

`lnurl pay --plan …` prepares checkout without paying automatically. Output starts with invoice not issued, settlement pending, and entitlement inactive. `pay-status` and `verify` ask the backend; invoice issuance never activates access. Comments are bounded by advertised `commentAllowed` and remain untrusted metadata. payerData auth is preferred, while email/name/identifier are never auto-filled. Validated successAction messages/URLs may be displayed but are never opened automatically.

`lnurl address name@domain` performs an explicit HTTPS discovery request without redirects. It shows routing metadata and never authenticates a Principal or sends payment. Lightning Address is routing UX, not identity.

## Withdraw

`lnurl withdraw` requires an installed PoP Session and calls the backend policy-gated endpoint. A QR/URI is emitted only when `policy_approved` is true. k1 validation, invoice validation, payout, replay prevention, limits, roles, step-up, and audit remain backend-controlled. The current backend has no Bastion-side withdraw status route, so `withdraw-status` reports that limitation rather than inventing local completion.

Operational failures mean unknown/pending—not success. Production readiness depends on callback security, configured settlement providers, revocation, Policy Engine, recovery, deployment, and real-wallet interoperability.
