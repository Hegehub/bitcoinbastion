# LNURL-auth Domain Policy

**Status: PARTIAL / production configuration required.**

LNURL linking-key identity must be scoped to an explicit stable authentication domain. It must never be derived from an arbitrary request `Host`, `Forwarded`, or `X-Forwarded-Host` value.

- **Production:** deployment must configure a dedicated allowlisted auth domain through the LNURL service configuration and ingress. No canonical production value is proven in this repository, so production promotion is blocked until operators record and validate it.
- **Staging:** uses an explicitly configured staging-only domain and separate linking namespace. Staging keys and Principals must not be silently promoted.
- **Development:** localhost/test domains are permitted only by explicit local-development URL policy. They do not establish production identity.
- **Migration:** publish old/new domain metadata, require fresh proof for the new namespace, create an audited backend policy-approved linkage, retain revocation history, and never merge by raw linking key, Lightning Address, email, or payment identifier.
- **Mismatch:** fail closed. The client must not offer “continue anyway.”

Domain changes require an issuer/policy epoch change, audit event, compatibility communication, and rollback/revocation plan.
