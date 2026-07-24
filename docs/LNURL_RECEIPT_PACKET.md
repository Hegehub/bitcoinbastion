# LNURL Receipt Packet

An LNURL Receipt Packet is verifiable payment evidence. It is not an authentication credential, an Access Pass, or a Subscription Entitlement.

The packet connects the LNURL-pay request, callback, issued invoice fingerprint, verified settlement evidence, Bastion LNURL Payment Proof, Subscription Entitlement or PayRegister context, Policy Engine decision, Audit Chain references, and optional Bastion issuer signature. Invoice issuance alone is never enough to create a completed receipt; settlement must be verified first.

## Packet lifecycle

1. A wallet resolves LNURL-pay or Lightning Address metadata.
2. Bastion issues an invoice through the existing LNURL callback flow.
3. Settlement is verified through LNURL-verify, an internal Lightning node, BTCPay, a provider callback, or preimage verification.
4. Bastion creates a Payment Proof.
5. Subscription entitlement or PayRegister context is attached by hash/reference only.
6. Policy and Audit Chain hashes are recorded.
7. The receipt service canonicalizes the packet, computes `packet_hash`, and signs it when issuer signing is configured.

## Schema and canonicalization

The signed core excludes mutable presentation fields, `packet_hash`, and issuer signatures. Canonical JSON uses the shared Bastion deterministic JSON helper, integer millisatoshi/satoshi amounts, stable timestamp serialization, and SHA-256 packet hashes.

## Visibility projections

Receipt packets support private, customer, merchant, business-audit, enterprise-evidence, and public-redacted visibility. Customer and public views use explicit allowlists and exclude raw preimages, raw payerData, raw comments, Access Passes, session tokens, wallet seeds, private keys, LNURL linking material, internal database IDs, and principal hashes.

## Subscription receipts

Subscription receipts include plan code, entitlement hash/status, activation state, validity period, payment amount, settlement timestamp, policy hash, and audit hashes. The receipt confirms payment evidence and entitlement issuance state; it does not grant entitlement by itself.

## PayRegister and merchant receipts

PayRegister receipts include pseudonymous workspace/store/terminal/shift/order/invoice hashes when applicable. Merchant Lightning Address receipts may include an approved public route alias or address hash, but Lightning Address is payment routing, not payer identity or merchant legal identity.

## Refund linkage

Refund and payout references point to separate LNURL-withdraw evidence. The original payment receipt remains immutable; refund completion requires a separately verified withdraw/payout flow and appended audit events.

## Limitations

This service does not claim tax/legal invoice compliance, does not provide non-repudiation beyond configured issuer signatures and evidence hashes, does not implement fake PQ signatures, and does not custody funds or handle wallet seeds/private keys.
