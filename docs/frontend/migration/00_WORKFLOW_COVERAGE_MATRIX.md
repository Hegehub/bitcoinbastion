# User and Operator Workflow Coverage Matrix

All workflows begin `NOT_STARTED`. Each must prove actor/start, success/denial/degraded/recovery/audit/privacy/a11y/offline/rollback as a vertical slice.

| Workflow | Actor and start | Success / denial / degraded | Prompt(s) and rollback |
|---|---|---|---|
| Public status, education, overview | visitor, direct route | attributed public read models; honest unavailable/static education | 13; disable live panels |
| Operations health/storage/incidents/SLO/jobs/recovery/data flow | operator with capability | named health fields; 401/403; stale provider and storage detail | 14–15; feature-flag panels |
| Market status/regime/signals/timeline/replay/evidence/narratives/sources/heatmap/similarity | visitor/operator | informational models; provider conflict and snapshot provenance | 16–20; fall back to tables/unavailable |
| Trace submit/report/events/graph/exposure/disagreement/evidence/proof | visitor with public address/report id | advisory report; validation denial; partial providers; no legal/consensus claim | 21–25; disable graph/export independently |
| Evidence packet/detail/chain/replay/diff/provenance/export/verify | visitor/operator | verifiable provenance; expired/missing packet; offline verification status | 26–29; retain textual verification |
| Access checkout/payment/certificate | customer with external wallet/payment proof | intent → settlement proof → entitlement; expiry/underpayment/conflict | 30; disable checkout UI, preserve status |
| Challenge/session/device/PoP/signing | entitled device holder | external signing only; replay/expiry/revocation denials | 31–32; terminate session and clear memory |
| Profile/limits/catalog/cost | entitled user | effective limits and estimate; rate-limit visible | 33; read-only unavailable |
| Wallet entitlement/history/change | wallet principal | effective entitlement; downgrade impacts confirmed | 34; disable mutations |
| Child keys/delegated passes | authorized principal + Human Intent | one-time secret reveal; scope denial; revoke audit | 35; revoke/clear and disable issuance |
| Recovery/rotation/cancel/lockdown/revocation/expiry | recovering principal/operator | quorum/step-up; no automatic recovery; durable audit | 36; cancel and invalidate local material |
| Policy catalog/check/simulate/executions | operator | simulation distinct from execution; Human Intent required | 37; simulation-only |
| Audit/signal review | auditor/operator | immutable event views; redacted export | 38; read-only disable |
| Treasury request review | authorized reviewer | review only, explicitly no execution | 39; feature flag off |
| Entities/watchlists | analyst/operator | scoped list; privacy/redaction and conflict | 40; disable mutation |
| Fees/on-chain/wallet health | visitor/operator | informational status; never wallet secret input | 41; static unavailable |
| Citadel/Sovereign Grid/privacy | operator/user | synthetic clearly labeled; privacy assessment limitations | 42; textual alternative |
| Plugins | operator | permission review; deny unsafe capability | 43; disable plugin UI |
| Webhooks/deliveries | operator | endpoint/delivery status; secret shown once only | 44; pause/delete with confirmation |
| Safe API Explorer | developer | allowlisted real calls; signed requests delegated safely | 45; public GET-only mode |
| LNURL/Business Lightning Address | operator/customer | operator workflow; callback remains protocol-owned | 46; disable UI, retain protocol |
| PayRegister merchant/receipt/payment proof | merchant, separate product entry | merchant-scoped proof and receipt; no core-nav merge | 47; `payregister_ui=false` |
| Cross-cutting privacy/a11y/perf/security/release | all | keyboard, reduced modes, CSP and revision evidence | 48–52; per-feature flags |
