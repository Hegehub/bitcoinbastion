# Wallet-first and LNURL observability

Wallet/LNURL telemetry extends the existing Prometheus endpoint and Kubernetes
ServiceMonitor. It is operational aggregate data only: the Audit Chain remains the
evidence layer and the Policy Engine remains the authorization authority.

## Privacy and cardinality

Every label passes through a controlled enum or allowlist. Unknown input becomes
`unknown`; arbitrary exception text and dynamic request paths are never labels.
Metrics must never contain wallet addresses, public/linking keys, principal hashes,
device/session/challenge identifiers, k1, invoices, payment hashes/preimages,
Lightning Address usernames, Access Passes, recovery material, payerData, comments,
or merchant/customer identifiers. Endpoint paths are collapsed into bounded groups.
Metrics emission is best-effort and exceptions are swallowed so telemetry cannot
block authentication, policy, payment, recovery, or payout processing.

## Metric groups

Wallet metrics cover challenge/proof/registration/login, principal creation, device
binding/revocation and aggregate active counts, PoP sessions/request verification and
replay rejection, and step-up outcomes/duration. LNURL metrics cover auth challenges,
callbacks, signatures and k1 lifecycle; pay request/invoice/payment transitions;
verify duration/outcomes; aggregate Lightning Address classes; staged withdraw;
payment-to-entitlement; payerData and successAction safety outcomes. Shared Access
metrics cover policy, revocation, recovery, canonical audit append, security alerts,
and aggregate Integrity Score bands.

Histograms use fixed seconds buckets from 10 ms through 30 seconds. Gauges are set
from aggregate repository counts only and never per actor. Counter resets are handled
with PromQL `rate()`/`increase()`.

## Dashboard and alerts

`grafana-dashboard-wallet-lnurl.json` visualizes aggregate Wallet proof, LNURL-auth,
k1, policy, entitlement, withdraw and integrity posture. Alerts cover replay spikes,
proof rejection spikes, Policy denials, settlement verification failures and withdraw
denials. Alert annotations contain fixed summaries—not identifiers or raw errors.

Suggested initial thresholds are intentionally conservative and require production
baseline tuning. A replay alert should trigger Audit Chain and Revocation Registry
review; metrics alone are not incident evidence. Silence only with an incident record,
owner and expiry. Validate dashboards/rules with `promtool` and Grafana provisioning
checks in deployment CI when those binaries are available.

