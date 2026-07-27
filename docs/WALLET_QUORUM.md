# Wallet/LNURL authority quorum

The quorum coordinator combines independently verified wallet, LNURL, device,
role, certificate, recovery, transparency, and issuer evidence. It does not
verify cryptography itself and it never grants access independently: the central
Access Policy Engine remains the final authority before satisfaction and action
execution.

## Security model

Every approval is bound to one canonical policy hash, action, Human Intent hash,
expiry, participant slot, principal commitment, underlying-key commitment, proof
method, and optional device/role commitment. The same principal, underlying key,
or device cannot count twice, including when different adapters expose the same
authority. Raw addresses, linking keys, signatures, session tokens, seeds, and
private keys are never quorum fields.

Policies specify thresholds, slot constraints, minimum distinct principals and
methods, required roles/methods/participant types, compatibility limits,
hardware/air-gapped requirements, PoP Session and Human Intent requirements,
Recovery Capsule and transparency requirements, TTL, cooldown, epochs, and
one-time consumption. Policies are canonicalized and hash-bound to every proof.

LNURL-auth proves a domain-specific Lightning linking key. It cannot satisfy
treasury ownership or issuer-key rotation. Legacy message signatures cannot
satisfy critical or Sovereign quorum. Hardware evidence counts only when an
existing verifier marks it cryptographically/attestation verified.

## Lifecycle and integrations

Attempts progress through pending, partially satisfied, satisfied, and consumed,
or terminate as expired, denied, revoked, cancelled, or locked. SQL row locking
serializes approval and consumption. Revocation checks cover the policy, attempt,
approval, principal, underlying key, device, and proof. One-time quorums are
consumed only after cooldown and a final Policy Engine allow decision.

Recovery Capsule uses `RecoveryCapsuleQuorumAdapter`; Wallet/LNURL step-up can
project a satisfied evaluation into its existing quorum state. Business policies
use distinct owner/admin slots. Enterprise, Sovereign, issuer rotation, large
payout, lockdown release, offline-root issuance, and high-assurance device
enrollment can impose stronger slots and evidence without endpoint-local logic.

Audit events contain commitments and controlled reason codes. Metrics use only
quorum type, action group, result, and reason category. A quorum is distributed
authority—not an authentication token, entitlement, scope, or bearer credential.

> Bastion never asks for a Bitcoin seed, mnemonic, xprv, WIF, or private key.
