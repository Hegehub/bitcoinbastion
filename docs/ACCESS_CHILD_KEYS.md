# Access Child API Keys and Delegated Passes

Bitcoin Bastion uses Child API Keys and Delegated Passes so operators do not put a Master Access Pass into scripts, bots, Telegram integrations, PayRegister devices, or temporary workflows.

## Terms

- **Master Access Pass**: display-once root access material used only to issue/lookup an Access Certificate. It is never a bearer token and must not be embedded in integrations.
- **Child API Key**: scoped API credential created under a parent Access Certificate and Subscription Entitlement. It is bounded by plan, scope, metric entitlement, expiry, quota, policy, revocation, and audit.
- **Delegated Pass**: temporary and narrower access grant for another actor/device/process. It is not a full Access Pass and cannot exceed the parent.

## Plan limits

| Plan | Child API keys | Delegated passes | Notes |
| --- | ---: | ---: | --- |
| Basic | 1 | 0 | read-only, short expiry, basic metrics only |
| Plus | 3 | 3 | standard market/trace and Telegram-style automation |
| Pro | 10 | 25 | Human Intent required for creation; no business/admin unless entitled |
| Business | 100 | 100 | role/device/cashier/operator keys, PayRegister by role |
| Enterprise | 1000 | 1000 | custom issuer/policy hierarchy and quotas |

## Required invariants

1. Child/delegated scopes must be explicit subsets of parent effective scopes.
2. `api:all`, `metrics:all`, `admin:all`, `*`, `root`, and `superuser` are forbidden.
3. Denied parent scopes cannot be reintroduced by a child key or delegated pass.
4. Expiry must be less than or equal to parent entitlement expiry.
5. Metric entitlements must be subsets of parent metric entitlements.
6. Plan limits must be enforced before creation.
7. Child/delegated credentials cannot delegate unless the parent explicitly allows delegation.
8. Parent revocation cascades to children and delegated passes.
9. Subscription downgrade freezes children/delegations that exceed the new entitlement.
10. High-risk credentials require request signing and/or Human Intent policy.

## Revocation and downgrade

Deleting a child key or delegated pass is a revoke operation, not a hard delete. Emergency Lockdown and parent-pass revocation freeze or revoke child material. Downgrades freeze any child/delegated material whose scopes are no longer covered by the current entitlement.

## Examples

- Bot market read key: `market:intelligence:read` with metric groups limited to parent market data entitlements.
- Telegram child-pass: short-lived Plus/Pro delegated pass with read-only alert scopes.
- Cashier delegated pass: Business pass with shift constraints and PayRegister invoice/shift scopes only.
- Analyst delegated pass: read-only Business reports with no treasury/admin/recovery privileges.

## Security rules

- Do not use a Master Access Pass in scripts.
- Store Child API Keys and Delegated Passes once; raw secrets are not shown again.
- Revoke unused keys.
- Use the narrowest possible scopes and expiry.
- Never request or enter a Bitcoin seed/private key.
- Raw child keys (`bbk_live_*`) and delegated passes (`bbd_live_*`) are never stored, logged, or audited.
