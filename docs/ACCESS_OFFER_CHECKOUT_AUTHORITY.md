# Access Offer and Checkout authority

## Trust boundary

| Field | Previous source | Authoritative owner | Caller sends? | Frozen in Checkout |
|---|---|---|---|---|
| offer ID | plan/query | Access Offer catalog | yes | yes |
| revision | absent | deterministic Offer Revision | no | yes |
| price/unit | caller/API table | Offer Revision | no | yes |
| duration | issuance caller | Offer Revision | no | yes |
| capability/scopes | plan services | Offer Revision | no | yes |
| terms version | absent | Offer Revision | no | yes |
| expiry | payment provider | Checkout backend | no | yes |
| payment amount | caller | frozen Checkout | no | yes |
| eligibility | implicit | Checkout state machine | no | yes |

The client selects only an `offer_id`, payment method, and retry identity. It cannot set price,
unit, duration, capability, scopes, terms version, expiry, or eligibility.

## Offer authority

The canonical catalog is versioned server configuration derived from established `PlanCode`, the
pre-existing sat price table, and plan entitlement scopes. Each stable Offer ID has a deterministic
revision ID over its exact price, unit, 30-day duration, terms version, and scopes. Changing any
semantic term creates a new revision identity; persisted Checkout snapshots never reread current
terms. Amounts are exact integer sats. Current offers are payment-backed and active; no caller-created
zero-price offer exists.

## Checkout Session

`access_checkout_sessions` persists a UUID identity, idempotency-key hash, exact Offer/revision,
frozen economics and entitlement intent, payment reference, timestamps, status, and typed eligibility
reason. The minimal state machine is:

| From | Event | To | Preconditions |
|---|---|---|---|
| awaiting_payment | verified settlement | eligible | not expired; bound payment is paid |
| awaiting_payment | expiry | expired | server time at/after expiry |
| eligible | A2 issuance | future A2 | A2 security ceremony; not implemented here |
| cancelled/failed/expired | any eligibility refresh | unchanged terminal | terminal state |

`eligible` means issuance may proceed; it never issues Access. Refresh derives settlement from the
existing payment authority and expiry from server time. Checkout creation is idempotent by a hashed
intent key. Reusing a key for another Offer is a conflict. One Checkout binds one Payment Intent, and
the Payment Intent amount is always copied from the frozen Offer snapshot.

The legacy payment-intent route remains temporarily compatible but caller amount is non-authoritative:
a mismatched value is rejected and the server amount is used. Canonical `/access/checkouts` contains
no amount, duration, capability, scope, or revision request fields. Existing historical payment intents
without a Checkout remain explicit legacy records; no Offer revision is fabricated for them.

## API and A2 boundary

* `GET /api/v1/access/offers`
* `GET /api/v1/access/offers/{offer_id}`
* `POST /api/v1/access/checkouts`
* `GET /api/v1/access/checkouts/{checkout_id}`

A2 receives exact revision, frozen price/unit, duration, capability/scopes, terms version, expiry,
payment reference, status, `issuance_eligible`, and a typed reason. Challenge, PoP, and final issuance
remain A2/Feature-67 responsibilities. No frontend eligibility calculation is permitted.

## Rollback

Rollback may remove the Offer catalog, Checkout service/table, new APIs, generated bindings, and
tests. Existing payments, Access grants, devices, challenges, sessions, and user data remain. The
legacy caller-priced path must remain mismatch-guarded or be disabled; rollback must never restore
caller-controlled economics.
