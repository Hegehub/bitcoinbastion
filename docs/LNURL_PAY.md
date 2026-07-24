# LNURL-pay Notes

## LNURL-pay Metadata

Bitcoin Bastion LNURL-pay metadata is descriptive payment context. It is committed into future invoice/payment evidence, but it is not a settlement proof, access grant, subscription entitlement, recovery factor, policy decision, role assignment, or identity binding.

Supported metadata MIME types are allowlisted:

* `text/plain` (mandatory, exactly one entry)
* `text/long-desc` (optional)
* `text/identifier` (optional Lightning Address-style payment UX identifier)
* `image/png;base64` (optional, bounded raw base64 PNG)
* `image/jpeg;base64` (optional, bounded raw base64 JPEG)

Metadata is serialized canonically as a JSON array of two-item arrays in this order: `text/plain`, `text/long-desc`, `text/identifier`, then image metadata. The committed metadata hash is `sha256:<lowercase-hex>` over the UTF-8 canonical JSON string.

Subscription templates cover `lite_pass`, `basic_pass`, `plus_pass`, `pro_pass`, `business_pass`, and `enterprise_pass`; the Basic plan is displayed as “Bitcoin Bastion Basic Pass”, never “Base”. These templates describe the selected subscription duration and high-level plan context only. Pricing, scopes, entitlements, policy authorization, and settlement verification remain separate services.

Lightning identifiers are normalized as Lightning Address-style identifiers with one `@`, no URL scheme, no query string, no fragment, no whitespace, no embedded credentials, and no internal wallet/principal identifiers. A Lightning identifier is payment routing UX only and is not treated as a Wallet Principal, user ID, entitlement key, or recovery factor.

PayRegister metadata uses merchant display names plus public order or terminal references only. It does not include customer identity, cashier personal names, email, phone numbers, Wallet Principal hashes, internal database IDs, or sensitive inventory/business metadata by default.

Optional image metadata is validated without fetching external URLs. Raw PNG/JPEG base64 must match the declared magic bytes and fit within the configured decoded-size limit. SVG, JavaScript, HTML, data URLs, and external image URLs are rejected.

Forbidden metadata content includes Access Passes, session tokens, raw LNURL-auth `k1`, raw LNURL keys or signatures, wallet/private keys, xprv values, seed or mnemonic phrases, issuer private keys, server peppers, recovery material, internal principal hashes, and claims that payment metadata itself activates access or proves payment settlement.

## LNURL-pay Callback Invoice Stage

The callback invoice service validates a persisted LNURL-pay request, the wallet-selected integer millisatoshi amount, optional bounded comments, declared payerData fields, and the stored canonical metadata hash before calling a trusted Lightning invoice provider. The callback cannot change the original plan, product, principal binding, amount range, or canonical metadata.

Invoice creation is idempotent for the same request, amount, metadata hash, comment hash, payerData hash, principal binding, and crypto epoch. A retry returns the same normalized invoice; a conflicting retry fails safely. The service persists invoice-issued state and audit evidence, but it does not mark settlement, create Payment Proof, issue Subscription Entitlement, issue Access Certificates, create PoP sessions, or activate API access.

Audit events for `lnurl_invoice_issued` include request and invoice reference hashes, amount, metadata hash, provider name, product/plan, optional principal hash, expiry, and invoice status. They do not include raw payerData, full comments, payment preimages, provider secrets, private keys, seeds, session tokens, or Access Pass material.

## commentAllowed and callback comments

Bastion treats LNURL-pay `commentAllowed` as an optional character-count capability advertised by server policy. Comments are disabled by default (`0`/omitted), and the effective limit is bounded by global, product, merchant/store, terminal, and payment-request policy. Missing policy values do not increase permissions.

The callback `comment` parameter is URL-decoded exactly once, normalized with Unicode NFC, checked against both character and byte ceilings, and rejected for NUL/CRLF/control characters or double-decoding patterns. Accepted comments are stored as hash-only metadata by default and never alter immutable LNURL metadata or invoice description hashes.

A comment is untrusted metadata. It cannot authenticate a principal, settle an invoice, create a Payment Proof, grant a Subscription Entitlement, change plan/scopes/quotas, approve refunds or withdrawals, complete recovery, or satisfy Policy Engine access requirements.

## payerData.auth binding

Bastion can advertise LNURL-pay `payerData.auth` with a 32-byte single-use `k1` challenge. The callback accepts only `auth.key`, `auth.k1`, and `auth.sig`; name, email, identifier, and pubkey personal fields are disabled by default. A verified payerData.auth proof binds the unpaid payment request to a Lightning Principal pseudonym only. It does not prove settlement, create a session, issue an entitlement, or authorize access.
