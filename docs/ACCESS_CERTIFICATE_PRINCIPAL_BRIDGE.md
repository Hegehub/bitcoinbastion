# Access Certificate Principal Bridge

The canonical bridge is `PrincipalAccessCertificateBridge`. It extends the existing
Access Certificate issuer; it does not introduce another issuer or authentication
path. Bitcoin, Lightning, multi-method, Business, Enterprise, and PayRegister owner
principals are supported only when explicitly selected by policy. Unknown principal
types fail closed.

> An Access Certificate is a signed, policy-limited access credential. It is not a
> bearer token and does not grant protected access without an active principal,
> device binding, PoP session, subscription entitlement, Policy Engine allow
> decision, and clean revocation state.

## Binding and issuance

The v2 payload binds commitments for the principal, wallet device, source
entitlement, policy epoch, and crypto epoch. Effective scopes and metric groups are
set intersections across the request, principal, entitlement, and policy. Expiry is
bounded by both entitlement validity and the configured certificate maximum.
Issuance rechecks revocation state while the relevant rows are locked and supports a
request-bound idempotency commitment.

Standard Bitcoin issuance requires BIP-322 or stronger proof. Lightning issuance
requires a verified stable LNURL-auth domain and cannot include on-chain treasury or
descriptor ownership scopes. LNURL-auth proves control of a domain-specific
Lightning key, not ownership of an on-chain treasury wallet. Compatibility
certificates are short-lived/restricted and cannot enable delegation or offline
packs. High-assurance profiles require fresh step-up; Business, Enterprise, and
Sovereign profiles also require quorum.

The certificate is device-bound, but no device private key is stored. The bridge
requires an active wallet PoP session and a verified request signature before
issuance. Existing session and Policy Engine checks remain authoritative on every
protected request.

## Export, lifecycle, and legacy credentials

Optional `bastion-pass.bbp` export is disabled unless configured and requires Human
Intent evidence. Its policy declares that device proof, PoP, online policy, and
revocation checks remain required. It contains no wallet seed, mnemonic, xprv,
private key, device private key, session token, or raw Access Pass.

Rotation never expands scopes. Principal unlinking freezes dependent certificates;
principal/device/entitlement/certificate revocation disables use. Existing
certificates without a principal-binding row remain `legacy_unbound` or
`legacy_device_bound`; the migration does not infer ownership from email, payments,
IP addresses, or device metadata. They require explicit proof and rotation for new
high-risk capabilities.

The issuer metadata remains crypto-agile, but no post-quantum signature is claimed
unless a supported suite actually produces and verifies it. Bitcoin and LNURL proof
remain classical ecosystem proofs. Bastion never requests a Bitcoin seed, mnemonic,
xprv, WIF, or private key.
