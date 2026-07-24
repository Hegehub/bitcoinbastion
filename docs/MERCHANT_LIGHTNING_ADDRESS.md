# Merchant Lightning Address

Merchant Lightning Address is multi-tenant payment-routing UX for PayRegister and Business workspaces. Lightning Address is not identity. Bastion never asks for wallet seed/private keys. Invoice creation does not mean payment settlement. Custom domains must be verified. Merchant payments remain subject to Policy Engine, settlement verification and audit.

Supported domain modes are Bastion-managed domains such as `store-123@payregister.bitcoin-bastion.com` and verified merchant-controlled custom domains such as `coffee@merchant.com`, `store@merchant.com`, `terminal-01@merchant.com`, and `donations@merchant.com`.

Custom domains can use DNS TXT verification at `_bastion-lnurl.<domain>` with `bastion-lnurl-verification=<token>` or HTTPS well-known verification at `/.well-known/bastion-lnurl-verification`. Verification stores only token hashes, requires HTTPS for clearnet, blocks private/loopback/link-local HTTP targets, and audits success/failure. Operator approval is disabled by default.

Merchant addresses can target a workspace, store, terminal, cashier shift, campaign, donation, subscription, or custom target. Cashier-shift addresses expire with the shift and never grant cashier identity or authorization.

LNURL-pay discovery returns `payRequest` metadata with millisatoshi bounds, a trusted callback URL, optional bounded comments, and privacy-first payerData. Metadata is deterministic and excludes raw workspace IDs, device secrets, policy state, customer PII, private merchant notes, and cashier personal data.

Settlement modes include merchant node, PayRegister node, BTCPay, Bastion proxy when explicitly allowed, and external provider. Bastion remains non-custodial by default and does not store node seeds, wallet seeds, private keys, macaroons, or invoice-signing secrets in merchant address records.

Comments and payerData are untrusted. Comments cannot authorize actions, select merchant workspaces, or change payment routing. payerData personal fields are disabled by default and must be explicitly enabled under policy with privacy warnings.

Revocation of a domain, address, settlement profile, terminal, or cashier-shift target stops new resolution and invoice creation while preserving audit and settled-payment evidence. Onion support is not implemented by default and remains disabled unless explicitly configured.
