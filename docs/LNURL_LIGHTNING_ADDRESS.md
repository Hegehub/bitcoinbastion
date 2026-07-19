# LNURL Lightning Address Service

Lightning Address is human-readable payment-routing UX over LNURL-pay. It is not identity, authorization, a Wallet Principal, a Lightning Principal, settlement evidence, a PoP session, or a Subscription Entitlement.

This prompt implements only the internal domain, repository, domain-policy, and service layer. The public `/.well-known/lnurlp/{name}` route belongs to Prompt 38.

## Security boundaries

- Address resolution creates an LNURL-pay descriptor, not a BOLT-11 invoice.
- Invoice creation still happens in the callback service.
- Settlement verification, Payment Proof creation, and Subscription Entitlement issuance remain separate later stages.
- Product mappings are server-side (`lite`, `basic`, `plus`, `pro`, `business`, `enterprise`); `sovereign` is reserved and is not a public subscription tier.
- Callback references are HMAC/opaque references and must not expose raw target IDs.
- Custom merchant domains must be verified before activation.
- Comments remain untrusted metadata and default to zero unless policy enables them.
- payerData remains minimal; email/name are not required.

## Target routing

The service supports subscription products, merchants, PayRegister stores, PayRegister terminals, donations, business invoices, and custom targets. Store, terminal, merchant, and invoice references are stored as hashes or public aliases rather than raw internal database IDs.
