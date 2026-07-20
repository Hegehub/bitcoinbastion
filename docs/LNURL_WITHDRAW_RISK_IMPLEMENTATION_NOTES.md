# LNURL Withdraw Risk Implementation Notes

This implementation provides production-shaped service boundaries with in-memory adapters for tests. Database-backed reservations, velocity counters, execution attempts, and reconciliation events should replace the adapters before enabling production mainnet payouts. The defaults fail closed: withdraw and mainnet withdraw remain disabled unless deployment configuration explicitly enables them with finite limits and a configured payout provider.
