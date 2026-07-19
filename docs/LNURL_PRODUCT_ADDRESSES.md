# LNURL Product Lightning Addresses

A Bitcoin Bastion product Lightning Address is a payment endpoint. It is not a user identity, authentication credential, authorization credential, or recovery factor.

## Supported product addresses

The versioned product registry maps first-party aliases on `bitcoin-bastion.com` to canonical access plans:

| Address | Plan | Billing | Default behavior |
| --- | --- | --- | --- |
| `lite@bitcoin-bastion.com` | `lite_pass` | monthly | Fixed-price LNURL-pay product |
| `basic@bitcoin-bastion.com` | `basic_pass` | monthly | Fixed-price LNURL-pay product |
| `plus@bitcoin-bastion.com` | `plus_pass` | monthly | Fixed-price LNURL-pay product |
| `pro@bitcoin-bastion.com` | `pro_pass` | monthly | Fixed-price LNURL-pay product |
| `business@bitcoin-bastion.com` | `business_pass` | monthly | Fixed-price payment with separate Business owner activation policy |
| `enterprise@bitcoin-bastion.com` | `enterprise_pass` | custom | Disabled / contract-only by default |

## Product and price authority

Product names, plan codes, billing periods, metadata, payerData policy, successAction policy, and amount ranges come from `config/lnurl_product_addresses.yaml` or an equivalent trusted signed catalog. Client callback amounts cannot select, upgrade, downgrade, or otherwise alter the server-authoritative plan.

For fixed-price products, LNURL discovery sets `minSendable == maxSendable == amount_msat`. The callback invoice service rejects amount mismatches and binds the issued invoice to the request metadata hash and product snapshot.

## Metadata

Product metadata is canonical JSON with deterministic ordering:

1. `text/plain` describes the exact product and billing period.
2. `text/long-desc` describes the product without user data or secrets.
3. `text/identifier` contains the canonical Lightning Address.

The metadata must not contain raw payment IDs, principals, invoices, session tokens, Access Passes, comments, payerData, recovery material, or internal database IDs.

## Privacy defaults

Product payerData defaults to optional `auth` and disabled personal fields. Email and name are not mandatory. Comments default to disabled (`commentAllowed = 0`) and remain untrusted metadata even when a future product enables them.

## Settlement before entitlement

Invoice issued does not mean payment settled. Product discovery and invoice creation do not issue Subscription Entitlements, Access Certificates, device bindings, PoP sessions, Business roles, or owner authority. Entitlements require settlement verification, LNURL Payment Proof issuance, principal binding where applicable, issuer signing, Policy Engine approval, and audit events.

## Enterprise and Business

Enterprise is contract-only by default and must not be activated by an arbitrary public invoice. Business payments may create subscription evidence or a pending onboarding flow, but payment alone must not assign Owner/Admin authority.

## Rotation and revocation

Every product has a product configuration hash and catalog epoch. Issued invoices retain their original snapshot. Disabled or revoked product versions cannot issue new invoices, and configuration changes should produce audit events.
