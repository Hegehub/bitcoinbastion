# Public API Security

Bitcoin Bastion uses Proof-of-Access authorization for protected APIs. Legacy email/password authentication is disabled.

Public status and marketing-safe endpoints may remain unauthenticated. Protected endpoints must require Proof-of-Access dependencies, request-signature verification where required, revocation checks, and an Access Policy Engine decision.

Bastion never asks for a Bitcoin seed, Bitcoin private key, recovery phrase, raw Access Pass as bearer proof, password, or mandatory email address for protected API authentication.

## Public versus premium boundaries

Public endpoints are limited to health/liveness, public landing/status, intentionally public trace-lite/address checks, public docs, and other non-sensitive read-only surfaces. Provider/internal health, operations dashboards, treasury, policy management, business trace, enterprise trace, webhook management, metrics usage, admin/operator, and developer-management endpoints require Proof-of-Access.

## Proof-of-Access boundary

Public endpoints do not require Proof-of-Access, but premium/private endpoints must require an active PoP session, request signatures when policy requires them, revocation checks, subscription entitlement checks, and a Policy Engine decision. Denied lower-tier requests should return structured errors such as `plan_upgrade_required`, `scope_not_allowed`, or `metric_not_allowed` rather than leaking premium data.

Error responses should be structured and safe to display. They must not expose raw entitlement internals, raw Access Passes, raw session tokens, recovery phrases, private keys, Bitcoin seed material, server pepper, issuer private keys, BTCPay API keys, or webhook secrets.

The stable frontend/API rule is: public data may be public; protected data requires Proof-of-Access. Access Passes are never bearer tokens.

## Public LNURL activation and receipt endpoints

Public activation and receipt endpoints must provide generic not-found behavior, rate-limit enumeration attempts, and return only safe status fields. They must not return raw invoices, preimages, activation references beyond the path input, Access Passes, PoP session tokens, wallet identifiers, LNURL linking keys, issuer private keys, merchant API keys, or unrestricted redirect URLs. A successAction URL is never authorization.


## Lightning Address discovery

`GET /.well-known/lnurlp/{name}` is a public LNURL protocol endpoint and returns the raw LUD-06 `payRequest` object rather than the Bastion API envelope. The route is read-only discovery: it does not create invoices, mark payments settled, create principals, issue PoP sessions, or grant Subscription Entitlements. Callback URLs are built from trusted LNURL configuration, not from untrusted `Host` or forwarded headers, and Lightning Address values are payment-routing aliases rather than user identity.
