# Access Subscription Entitlement Overlays

Subscription Entitlement Overlays define the active commercial and technical access surface for Bastion Proof-of-Access Auth. The Access Certificate proves that an Access Pass exists and is bound to a device key; the entitlement overlay defines what that access right can do right now.

## Why overlays exist

Bitcoin Bastion must not reissue a full Access Certificate every time a subscription renews, upgrades, downgrades, expires, freezes, or changes limits. Instead, the base certificate remains the signed access right and the Subscription Entitlement Overlay carries the plan, status, scopes, metric groups, limits, validity window, and issuer signature.

## Plan matrix

Canonical plans are `lite_pass`, `basic_pass`, `plus_pass`, `pro_pass`, `business_pass`, and `enterprise_pass`. Each plan uses explicit metric groups and API scopes. No plan, including Enterprise, uses wildcard permissions such as `api:all`, `metrics:all`, `admin:all`, or unrestricted access.

## Metric groups and limits

Entitlements include signed metric group lists, daily/monthly metric credits, history limits, minimum intervals, websocket stream limits, child API key allowances, delegated pass allowances, and batch query availability. Effective access must be calculated from the stored signed entitlement, not from user-submitted plan names.

## Upgrade and downgrade behavior

Upgrades create a new entitlement overlay with expanded plan scopes and metric groups. They do not automatically expand existing child API keys. Downgrades create a new entitlement overlay with reduced scopes, reduced metric groups, and metadata indicating child key / delegated pass review is required until those services exist.

## Security rules

- Payment is not login.
- Access Pass is not a bearer token.
- Password and email are not required for entitlement issuance.
- Bitcoin seed phrases and Bitcoin private keys are never accepted.
- Raw Access Pass values, payment secrets, private keys, recovery phrases, and session tokens are never stored in entitlement rows or public responses.
- Revoked and expired entitlements deny protected access.
- Frozen entitlements return restricted/frozen decisions for future Policy Engine use.
