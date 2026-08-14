# Prompt 12 — Trace Submit and Authoritative Report

## Canonical ownership

Repository Feature Register authority assigns **Feature 21 — Trace safe submit** and
**Feature 22 — Trace advisory report** to this bounded stage. Features 23–26
(graph, topology/privacy/disagreement, and proof work) remain Prompt 13+ scope.

| Feature | Surface | Operation | Contract | State owner | Evidence |
|---|---|---|---|---|---|
| 21 | `/trace` | `submit_trace_api_v1_trace_submit_post` | `TraceSubmitRequest` → `TraceSubmissionResult` | `TraceState` | contract/idempotency tests; generated ownership |
| 22 | `/trace/[report_id]` | `get_report_api_v1_trace_report__report_id__get` | `TraceReport` | `TraceReportState` | adapter/state/component tests |

## Operation and mutation authority

| Class | Method/path | Security | Human Intent / PoP | Idempotency | Processing |
|---|---|---|---|---|---|
| SUBMIT | `POST /api/v1/trace/submit` | Canonically public Feature-21 address workflow | Not required by current backend metadata | Required `Idempotency-Key`; SHA-256 only is persisted; replay returns the original report; conflicting payload is 409 | T1 synchronous |
| REPORT | `GET /api/v1/trace/report/{report_id}` | Canonically public advisory report | Not applicable | Read-only | Completed persisted report |
| FUTURE | graph/privacy/disagreement/proof operations | Existing operation-specific policy | Prompt 13/14 | Not evaluated here | Out of scope |

Trace Submit supports exactly the explicit `BITCOIN_ADDRESS` subject discriminator
on the deployment's `bitcoin-mainnet` context. Frontend trimming/shape checking is
advisory; `TraceService` remains the authoritative validator and normalizer. Submit
is audited by the existing `trace.report.created` outbox event. The same key and
same normalized subject resolve to one persisted report; a deliberate new attempt
uses a new key. No automatic mutation retry is performed.

## Conclusion ownership and privacy

| UI fact | Backend field | Frontend transform |
|---|---|---|
| identity | `TraceReport.id` | decimal text / route identity |
| analyzed subject | `TraceReport.address` | display/wrap only |
| status | `TraceReport.status` | exact enum-like text |
| summary | `TraceReport.summary` | exact text |
| advisory band / score | `trace_band` / `trace_score` | exact text; never probability or legal label |
| confidence | `confidence` | exact number; no recomputation |
| source posture | `source_quality` / `freshness` | exact text |
| limitations | `limitations` | safe joined text |
| Evidence references | `evidence_refs` | reference text only; never “verified” |

The Feature-54 projection is an explicit allowlist. Raw report dictionaries,
factor contributions, provider payloads, internal metadata, credentials, node
URLs, heuristics, and Proof Packet bodies do not enter canonical Reflex State.
`frontend_trace_conclusion_recomputations = 0`.

## Lifecycle, accessibility, degraded behavior

Submit is synchronous: ready → submitting → backend-generated identity → report
navigation. The disabled button prevents accidental concurrent activation while
durable backend idempotency remains authoritative. Back/forward and report refresh
only issue report reads and cannot resubmit. Route entry validates the opaque report
identity and loads it from the backend.

The form has a persistent label, description, named submit action, text validation,
and deterministic pending state. Report content uses textual identity/status,
summary, confidence, limitations, and Evidence-reference caveats. Long identifiers
wrap in existing responsive cards. LIVE backend responses remain distinct from
processing status; deterministic fixtures, when used by tests, remain
`DEMO_FIXTURE`. Unsupported/rate-limited/unavailable submissions preserve the input
and require explicit retry with the same attempt identity.

## Rollback

Revert the Prompt-12 commits and migration `20260812_0073`. This preserves all
Prompt 9–11 Market work, Feature 52/54/67, Stage-4 WS, shell/routes, and existing
Trace reports. Rollback must restore an honest unavailable submit posture—not the
legacy stateful raw-dictionary report or a non-idempotent mutation.
