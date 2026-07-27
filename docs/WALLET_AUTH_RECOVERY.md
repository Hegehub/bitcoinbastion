# Wallet-first Recovery Capsule

> **Bastion will never ask for your Bitcoin wallet seed, mnemonic, xprv, WIF,
> or private key.**

Recovery Capsule is the policy-controlled replacement for password/email reset,
support reset, payment-only recovery, bearer Access Pass restoration and reusable
recovery tokens. It stores only principal/capsule commitments, factor fingerprints,
states, epochs and safe audit metadata.

## Profiles and factors

Declarative profiles cover Lite/Basic, Plus, Pro, Business, Enterprise and Sovereign.
All require a principal-bound proof plus supporting evidence and cooldown. Pro adds a
recovery-file commitment and trusted-device history. Business requires owner evidence
and a role quorum. Enterprise requires multi-method quorum, verified hardware evidence
and a transparency checkpoint. Sovereign requires an offline kit, transparency and a
multi-wallet or multi-method quorum. No support operator can satisfy or waive factors.

Supported factor identifiers include BIP-322, LNURL-auth, verified payment or active
entitlement continuity, trusted-device history, recovery-file commitment, Access
Certificate, verified hardware/air-gapped evidence, owner/admin/operator evidence,
offline kit, transparency checkpoint, cooldown/time delay and quorum boundaries.
Payment settlement is only supporting continuity evidence and cannot independently
recover access. Lightning Address, payerData email, comments, invoices, Telegram,
cookies and IP addresses are not factors.

LNURL-auth recovery uses a dedicated `action=auth` challenge internally bound to
`recovery_factor_verify`, the capsule hash, policy hash, stable auth domain and
profile. Its 32-byte k1 is short-lived and atomically single-use. The callback
reuses the canonical LNURL signature verifier, checks the pre-linked Lightning
Principal commitment and revocation state, and records one signed, non-bearer,
attempt-bound factor receipt. It does not issue a session or invoke completion.
Full multi-wallet/multi-method quorum cryptography is **not implemented here**. The
quorum verifier protocols are the Prompt 59 integration boundary. Unsupported or
unregistered factors fail closed.

Lite/Basic still require payment or entitlement continuity. Plus/Pro require
recovery-file and trusted-device evidence according to profile. Business requires
a distinct role quorum and freezes roles. Enterprise accepts LNURL-auth only as
supporting evidence alongside hardware, multi-method quorum and transparency.
Sovereign treats it as optional convenience evidence; offline material,
multi-method or multi-wallet quorum, and transparency remain mandatory. A linking
key is domain-specific classical secp256k1 proof—not Bitcoin treasury ownership,
hardware assurance, legal identity, or post-quantum proof.

Public challenge-start responses are generic to resist principal, entitlement,
workspace and capsule enumeration. Callback failures use one LNURL-compatible
error shape. Audit and metrics contain only commitments and bounded labels; they
exclude raw k1, linking keys, signatures and recovery material. Changing the
stable auth domain requires an explicit, audited security migration.

## Workflow and cooldown

The explicit state machine progresses from created to awaiting factors, factor
verification, cooldown, ready-for-completion and completed. Failed, cancelled,
expired and revoked are terminal; locked requires a future separate high-assurance
unlock policy. Illegal transitions are rejected.

Minimum cooldowns are 30 minutes (Lite/Basic), 2 hours (Plus), 6 hours (Pro), 12
hours (Business), 24 hours (Enterprise) and 48 hours (Sovereign). Risk, failures and
recent security changes only extend these values. Capsule creation is rate-limited,
attempts are capped, proof-reference commitments are replay checked, and maximum
attempts lock the capsule. There is no support or production cooldown bypass.

## Completion and resulting access

Completion locks/reloads the capsule, checks expiry, factors, freshness/replay and
revocation, checks quorum where required, enforces cooldown, and requires a final
Policy Engine authorizer. The same transaction invokes the artifact manager, updates
the capsule and appends canonical audit events. Plus and higher profiles revoke old
sessions and freeze child/delegated artifacts by policy boundary.

Successful recovery returns only a `recovery_only` session boundary. It cannot create
API keys, increase scopes, change treasury policy, administer PayRegister, export
sensitive data, assign roles, release lockdown, issue offline packs, delegate access,
or administer payouts. Fresh high-assurance step-up and a new Policy Engine decision
are required to leave recovery mode.

## Existing recovery compatibility

The earlier Access recovery service and encrypted user-controlled recovery material
remain readable for migration, but its generated “Recovery Seed” terminology is
deprecated and must not be confused with a Bitcoin wallet seed. Recovery files and
vault commitments may be adapted as factors. Recovery codes, pass-only, payment-only
and support-controlled completion are forbidden from bypassing Recovery Capsule.
Legacy public endpoints must be migrated to this policy boundary before production
enablement; public routes themselves are deferred to Prompt 64.

Audit events contain hashes/fingerprints only. Revocation checks cover capsule,
principal, factors, device, entitlement, certificate, recovery files, offline kits,
quorum and transparency objects. Metrics use profile/type/result/reason classes only.
