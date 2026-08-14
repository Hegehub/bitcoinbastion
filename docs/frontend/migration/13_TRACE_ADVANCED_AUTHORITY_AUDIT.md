# Prompt 13 advanced Trace authority audit

Status: **BLOCKED — authority is insufficient for an implementation that does not
invent forensic meaning in the browser.**

Prompt-13R stop code:

`FEATURE23_ANALYTICAL_RELATIONSHIP_SOURCE_MISSING — Trace analysis accepts one
public address and produces report-level scores, classifications, and aggregate
UTXO amount statistics, but it produces no authoritative relationship between
two stable analytical subjects.`

This audit is the Prompt-13 pre-implementation stop record. It deliberately adds
no topology route, graph state, fixture, or browser projection. Doing so from the
current contracts would violate the default-deny and backend-authority rules.

## Canonical feature ownership

The canonical feature register supersedes its provisional labels and assigns the
following definitions to Prompt 13.

| Feature | Canonical name | Existing state | Prompt-13 responsibility | Required evidence |
| --- | --- | --- | --- | --- |
| 23 | Graph focus, pin and isolate | No Trace topology producer, contract, or route | Focus/pin/isolate only after authoritative topology exists | Named DTO fields, degraded states, DOM and accessibility evidence |
| 24 | Semantic graph edge types | No Trace edge model or relation taxonomy | Render backend-authored edge types without inference | Typed edge identity, direction, relation and DTO-to-DOM proof |
| 25 | Node pulse driven by freshness | Trace-report freshness exists, but no node freshness authority exists | Presentation driven by per-node backend freshness, with static reduced-motion mode | Typed node freshness and browser/reduced-motion evidence |
| 26 | Graph time travel | No Trace capture/version model, storage, or read operation | Render an immutable backend historical capture | Stable capture identity, historical DTO, refresh and no-future-leakage evidence |

## Advanced Trace authority matrix

| Concept | Producer | Storage | Operation / DTO | Historical authority | Privacy posture | Classification |
| --- | --- | --- | --- | --- | --- | --- |
| Trace report | `TraceService.analyze_address` | `trace_reports` scalar and JSON columns | `GET /trace/report/{report_id}` / strict `TraceReport` | Current report only | Existing Prompt-12 allowlist | Supporting foundation |
| Graph nodes | None | None | None | None | Undefined | `INSUFFICIENT_AUTHORITY` |
| Graph edges | None | None | None | None | Undefined | `INSUFFICIENT_AUTHORITY` |
| Node freshness | None | None | None | None | Undefined | `INSUFFICIENT_AUTHORITY` |
| Graph expansion | None | None | None | None | Undefined | `NOT_APPLICABLE` |
| Historical Trace capture | None | None | None | None | Undefined | `INSUFFICIENT_AUTHORITY` |
| Provider disagreement | `ProviderDisagreementService` | `provider_disagreement_json` | Generic `dict[str, object]` response despite a typed internal producer model | Report creation time only; no capture identity | No browser-specific safe response model | `UNSAFE_FOR_BROWSER` |
| Privacy shield | `PrivacyShieldService` | `privacy_shield_json` | Generic `dict[str, object]` response despite a typed internal producer model | Report creation time only | No API-level default-deny projection or sensitivity classification | `UNSAFE_FOR_BROWSER` |
| Proof/evidence workspace | Existing future endpoints | Existing report/evidence storage | Prompt-14/15 operations | Out of scope | Out of scope | `FUTURE_PROMPT_14` / `FUTURE_PROMPT_15` |

## Prompt-13R authority-gap matrix

| Capability | Current producer | Current storage | Current API | Type-erasure point | Missing authority | Required canonical owner |
| --- | --- | --- | --- | --- | --- | --- |
| Node / node identity / node type | `TraceService` validates one address | `TraceReport.address` | Report DTO | None for the report subject | No second analytical object and no topology node taxonomy | Trace analytical engine, then topology projector |
| Edge / source / target / direction / relation | None | None | None | Not applicable | No relationship fact or direction semantics | Trace analytical relationship producer |
| Amount / path / completeness / limitation | Aggregate UTXO amount lists are accepted by privacy helpers but the canonical Trace flow supplies `None` | Aggregate privacy JSON | Generic privacy dictionary | Typed privacy model is dumped to JSON and read as a dictionary | No outpoint identity, input/output relation, path, or topology scope | Trace analytical relationship producer and topology projector |
| Completed Trace state | `TraceService.analyze_address` | Mutable report row plus JSON metadata | Current report read | Several advanced fields become dictionaries | Report state exists, but contains no topology | Trace analysis aggregate |
| Capture ID / time / schema / method / source revision / integrity | None | None | None | Not applicable | No capture boundary or immutable semantic payload | Immutable Trace capture service/repository |
| Disagreement subject / claim / alternative / source / confidence / resolution | `ProviderDisagreementService` compares caller-supplied label and risk-band lists | Generic JSON column | Generic dictionary response | `model_dump` → JSON → `dict[str, object]` | Alternatives and their source identities/observed times are discarded; current canonical Trace call supplies one unknown label and one risk band | Trace provider-claim producer plus typed disagreement projection |
| Privacy class / browser allowlist / redaction | `PrivacyShieldService` produces aggregate advisory fields | Generic JSON columns | Generic dictionary responses | `model_dump` → JSON → dictionaries | No field sensitivity taxonomy or versioned safe-browser contract | Backend privacy policy and safe projection |

## Analytical-source inventory

The Prompt-13R repository-wide producer audit classified the available candidates
as follows:

| Candidate | Classification | Reason |
| --- | --- | --- |
| `TraceService.analyze_address` | `REPORT_SUMMARY_ONLY` | Its input is one address; it invokes baseline scoring with zero evidence and persists no related subject. |
| `TraceReport` and its JSON metadata | `GENERIC_METADATA` | They store report-level conclusions and aggregates, not node adjacency or a relationship observation. |
| `PrivacyShieldService` UTXO input | `INSUFFICIENT_FOR_TOPOLOGY` | The input is only `list[int]` amounts, has no txid/outpoint identity, and the canonical Trace flow passes `None`. |
| `OnchainEvent` | `INSUFFICIENT_FOR_TOPOLOGY` | It records a txid, address, and amount observation, but defines no Trace-report association, input/output role, outpoint, counterparty, or directed relationship. Treating co-occurrence as an edge would invent semantics. |
| `TraceEvidence` | `REPORT_SUMMARY_ONLY` | It references evidence text but does not identify two related analytical subjects or a directed relation. |
| Frontend Trace components | `FRONTEND_ONLY` | Presentation copy cannot establish backend forensic authority. |
| Tests/fixtures | `TEST_ONLY` | They cannot become production analytical truth. |

The first missing link is therefore not a topology schema or projector. It is the
**analytical relationship producer itself**. A projector can only preserve facts
that an upstream analysis owns; it cannot turn address/transaction co-occurrence,
aggregate UTXO amounts, evidence references, or timestamps into a defensible
`source → relation → target` fact.

## Strict-stop consequence

Prompt-13R explicitly authorizes projections and captures from **existing
authoritative Trace analytical facts**, but explicitly requires this stop when no
stable relationship exists. Creating a single address node with no edges would
not satisfy Feature 24, and creating an edge from `OnchainEvent.txid` and
`OnchainEvent.address` would assert an undefined input/output/flow relationship.
Likewise, creating immutable captures now would freeze only the report summary,
not the required Feature-26 graph state, and would not unblock Graph time travel.

The smallest safe remediation is an analytical-engine change that emits a typed,
source-backed relationship observation with stable endpoint identities, network,
direction, relationship type, integer amount/unit where applicable, observation
time, source reference, confidence/limitations, and an explicit completeness
scope. Once that exists, the authorized topology projector, capture persistence,
typed disagreement alternatives, privacy projection, Stage-1 regeneration, and
frontend work can proceed without inventing forensic conclusions.

## Concrete authority blockers

### Feature 23 — no topology producer

There is no Trace-specific node or edge persistence model, topology service,
topology API operation, generated topology DTO, or stable node/edge identity.
The existing `TraceReport` stores report-level conclusions and opaque JSON
metadata; it cannot establish adjacency, direction, path membership, or graph
completeness. A frontend graph would therefore manufacture topology.

Smallest safe remediation: add a backend-owned, bounded topology aggregate with
strict node and edge discriminators; stable IDs; explicit source/target and
direction; relation taxonomy; integer satoshi/explicit unit semantics; path and
completeness fields; limitations; and an operation-specific safe response model.

### Feature 24 — no semantic edge authority

No backend contract defines edge identity, direction, relationship type,
multi-edge behavior, self-edge behavior, or value unit. Report-level provider
disagreement cannot substitute for edge semantics.

Smallest safe remediation: define and test a strict backend edge model and have
the topology producer, rather than a serializer or frontend adapter, populate it.

### Feature 25 — report freshness is not node freshness

The current report has one report-level freshness value. There are no nodes and
no per-node observed/freshness timestamp. Reusing report freshness for every
hypothetical node would falsely imply node-level authority.

Smallest safe remediation: the topology producer must supply explicit per-node
freshness semantics (including unknown), after which the frontend may map the
enum to a static marker or reduced-motion-safe pulse.

### Feature 26 — no historical capture authority

Trace persistence has mutable report rows and source snapshots, but no topology
capture ID, report/topology version, immutable payload, capture timestamp, or
historical read operation. Market replay captures are a different domain and are
not reusable Trace authority. Filtering a present graph by time would be
pseudo-history and could leak future discoveries.

Smallest safe remediation: persist immutable Trace topology captures keyed by
Trace ID and opaque capture ID, record schema/analysis version and capture time,
and expose a strict historical read that returns only facts known at that capture.

### Disagreement and privacy — typed producers lose type safety at the API

Internal `ProviderDisagreementResult` and `PrivacyShieldReport` models exist, but
their service getters deserialize database JSON to dictionaries and the API
declares generic dictionary response models. The disagreement model also lacks
typed alternative claims (claim value, source, observation time, and resolution),
so it cannot support the required faithful comparison view. The privacy endpoint
has no browser-specific allowlist or field-level sensitivity policy.

Smallest safe remediation: validate persisted JSON back into versioned strict
domain schemas; define typed disagreement alternatives; define a backend safe
privacy projection that excludes internal fields by construction; expose those
strict response models; then regenerate the complete affected Stage-1 family.

## Ownership invariants preserved by stopping

| Invariant | Result |
| --- | --- |
| `frontend_trace_graph_semantic_inference_count` | `0` |
| `frontend_trace_historical_reconstruction_count` | `0` |
| `frontend_trace_disagreement_calculations` | `0` |
| `browser_received_trace_private_fields_not_required_for_ui` | `0` for new Prompt-13 work |
| `default_deny_trace_privacy_projection` | No new projection is opened |

Frontend-owned layout fields would be limited to `x`, `y`, zoom, viewport, and
label placement. They would have no analytical meaning. No such layout is added
until authoritative topology exists.

## Gates and evidence disposition

The semantic handoff preflight is valid. Prompt-12 regression tests may continue
to prove Submit/Report foundation, but browser topology/history evidence cannot
truthfully be produced because there is no operation to call. The first failing
acceptance gates are P13-A08/P13-A09 (topology producer and strict API), followed
by P13-A31–P13-A35 (historical authority) and P13-A53–P13-A55 (privacy-safe API
projection). No downstream graph, accessibility, responsive, or browser gate is
marked implemented or verified.

## Independent rollback

Rollback this audit commit only. It changes no schema, persistence, route,
generated client, frontend State, or user data. Prompt-12 Trace Submit/Report,
Prompt-9–11 Market behavior, Features 52/54/67, Stage-4, flags, shell, and the
protected generated transport remain untouched. A future rollback of a proper
Prompt-13 implementation must return to this fail-closed/no-graph posture, never
to generic graph dictionaries, browser inference, or private-field leakage.
