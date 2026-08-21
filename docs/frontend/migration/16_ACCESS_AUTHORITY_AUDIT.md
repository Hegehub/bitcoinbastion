# Prompt 16 — Access checkout/issuance/challenge/PoP authority audit

## Result

**A1 backend authority implemented; A2 frontend/security ceremony remains pending.** The backend now exposes deterministic versioned Offers and persistent Checkout Sessions with frozen server-owned economics and eligibility. Production Prompt-16 UI remains intentionally out of A1 scope.

> The blocker analysis below is retained as historical evidence of the pre-A1 state and is superseded by `docs/ACCESS_OFFER_CHECKOUT_AUTHORITY.md`.

## Canonical ownership

The current execution plan assigns Prompt 16 the mandatory **Access
checkout/issuance/challenge/PoP session** workflow. The Feature register's historical Feature 30/31
labels were superseded by unrelated Operations features and therefore are not reused. Prompt 17
owns profiles, limits, entitlements, and delegation; Prompt 18 owns recovery, lockdown, and
revocation.

| Capability | Existing backend authority | Prompt-16 responsibility | Non-goal | Required proof |
|---|---|---|---|---|
| Access acquisition | payment intent and plan enum | versioned offer plus checkout boundary | browser pricing | offer→DTO→VM→DOM |
| Certificate issuance | paid-intent certificate issuer | safe idempotent issuance UX | frontend grant creation | one issuance, retry same outcome |
| Challenge | persisted AccessChallenge | safe challenge UX | frontend nonce | expiry/replay/device tests |
| PoP session | AccessSessionService | approved device-provider integration | private key in State/server | signature→verifier→session |

## Existing backend inventory

* `PlanCode` and an API-local `_PLAN_PRICES_SATS` mapping exist, but there is no Offer model,
  offer ID, terms version, offer read operation, availability contract, or duration tied to an offer.
* `AccessPaymentIntent` is persisted and payment state is backend-owned. BTCPay is optional; manual
  grants are environment-gated. Invoice creation is not settlement and settlement is not issuance.
* `AccessCertificateIssuer` issues once for a paid intent and returns the raw Access Pass once. A
  repeated request returns the existing certificate summary without returning the secret again.
* `AccessChallengeService` persists a server nonce hash and canonical payload, binds certificate,
  origin, scopes, and device fingerprint, enforces expiry, and marks successful use once.
* `AccessSessionService` verifies Ed25519 device possession, checks certificate/device/entitlement,
  consumes the challenge, stores only an HMAC session hash, and returns a short-lived token once.
* Device private keys are not accepted by any Access request schema and are not persisted server-side.

## Concrete authority blockers

### ACCESS_OFFER_AUTHORITY_MISSING

`POST /api/v1/access/payment-intents` currently accepts `amount_sats` from the browser. The handler
uses that caller value when present instead of an immutable backend Offer. The API-local price map
is not a versioned offer contract and cannot support terms-change, availability, duration, or
stable offer identity proof.

Affected gates: P16-A05–A12, A43, A57, A74, A90, A101 and all checkout request-to-DOM gates.
Smallest safe remediation: add a backend Offer domain/read DTO with stable offer ID, price,
currency, duration, scopes, availability and terms version; create payment intents only from that
ID/version and reject caller-controlled price.

### ACCESS_CHECKOUT_STATE_MACHINE_UNDEFINED

`AccessPaymentIntent` is a payment lifecycle, not the required Checkout Session. There is no stable
checkout identity/version binding or canonical state joining offer, payment, device context,
issuance eligibility and limitations. `subscription_period_days` is also supplied by the issuance
request rather than frozen offer terms.

Affected gates: P16-A08–A16, A36, A44, A58, A64 and browser checkout/refresh/deep-link gates.
Smallest safe remediation: introduce a typed Checkout Session that snapshots offer terms and owns
valid transitions; bind payment and certificate issuance to it.

### PROMPT16_REQUEST_TO_DOM_REGRESSION

The current `/access` components are static explanatory cards. Plan cards build a query parameter
from hard-coded caller input; no Feature-54 offer/checkout/challenge/PoP/issued-access ViewModels or
request-owning Access State exists. The Feature-67 inventory explicitly deferred the approved
Access/session provider to Prompt 16.

Affected gates: P16-A57–A67, A74–A99 and A100–A125.
Smallest safe remediation after backend authority exists: promote the canonical Access operations
through Stage-1, add strict adapters and State, and integrate the existing secure device provider;
never store a private key or raw Access Pass in Reflex State.

## Existing operation-security matrix

| Operation | Class | Auth/capability | PoP | Human Intent | Idempotency | Replay |
|---|---|---|---|---|---|---|
| create payment intent | mutation | public acquisition boundary | no | explicit checkout click | missing checkout key | provider event dedupe only |
| read payment intent | read | public safe reference | no | no | n/a | n/a |
| issue certificate | mutation | paid-intent eligibility | no pre-issuance PoP | explicit issuance request | paid intent issues once | existing secret shown once |
| create challenge | mutation | active certificate/entitlement | device reference | explicit session intent | new challenge each call | server nonce/expiry |
| create session | mutation | active certificate/device/entitlement | Ed25519 required | signed challenge | one challenge use | used challenge rejected |
| read `/me` | read | PoP session | request security policy | no | n/a | session validation |

Challenge success proves device-key possession only. It does not prove payment, entitlement,
certificate validity, authorization, or Claim truth. Payment success is distinct from certificate
issuance, and certificate issuance is distinct from PoP-session creation.

## Verification performed

* Semantic handoff: `VALID_UNCHANGED_SOURCE`, 219 operations, 380 schemas.
* Focused Access integration/contract/unit/security suite: 102 passed.
* Existing tests confirm show-once certificate secret behavior, paid-intent enforcement, challenge
  replay rejection, origin/scope/device checks, session hashing, and absence of password/seed auth.
* No browser acceptance is claimed: a real offer/checkout authority and approved request-to-render
  provider do not exist, so mandatory browser proof cannot truthfully execute.

## Privacy, non-custody, and rollback

No wallet/custody behavior was added. Do not put Access Passes, session tokens, challenge
signatures, payment secrets, or device private keys in URLs, DOM, logs, fixtures, or Reflex State.
The synthetic `ACCESS_SECRET_CANARY_NEVER_BROWSER` was not introduced into runtime objects because
there is no safe projection implementation to test yet.

Rollback this audit independently. It changes no Access records, device identities, payment
intents, certificates, entitlements, challenges, sessions, generated transport, Feature-67
infrastructure, Prompt 13–15 behavior, or user data. A future implementation must fail unavailable
rather than falling back to static prices, frontend issuance, replayable challenges, or unsafe key
storage.
