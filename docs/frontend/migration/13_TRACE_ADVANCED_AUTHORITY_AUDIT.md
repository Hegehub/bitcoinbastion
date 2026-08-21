# Prompt 13 advanced Trace authority audit

## D3R remediation result and new request-to-render blocker (2026-08-15)

The two D3 infrastructure blockers documented below are repaired. GS1 persistence now
stores strict, digest-protected immutable Graph payloads with report, topology, and
Claim-capture linkage; exact reads reject missing and cross-report identities. A
centralized default-deny Trace Privacy Policy now owns Graph, Claim, Disagreement,
source, and provenance projection. Historical disagreement reads validate the exact
Graph Snapshot before evaluating its immutable report-captured Claims. Stage-1's schema
compiler now supports the strict discriminated Claim-value union, and generated output
is deterministic.

Repository inspection then proved a new, deeper request-to-render blocker. The frozen
scope claims that an existing Prompt-13 topology/history UI is available for minimal
adapter updates, but current frontend truth has no Trace Graph topology component,
Historical Trace ViewModel, Graph/history State, snapshot route/deep-link, node/edge
inspector, or stable-identity marker surface. The Trace report page contains only the
Prompt-12 report panels, and its disagreement panel is a static baseline placeholder.
Building the complete topology renderer, inspectors, accessible alternative, keyboard
navigation, mobile layout, history routing, stale-response lifecycle, and browser
harness would be a new frontend foundation—not integration with an established frozen
Prompt-13 UI.

The exact new stop condition is:

`D3R_PROMPT13_TOPOLOGY_UI_FOUNDATION_MISSING — persisted exact Graph/history and safe
typed disagreement contracts now exist, but the repository contains no production
Trace Graph topology/history request-to-render foundation to receive them; the frozen
"existing Prompt-13 topology UI" prerequisite is absent.`

Affected remaining gates are D3R-A70–A84, A94–A97, A106–A109, A113–A116. Backend
snapshot/privacy/history gates are covered by focused tests; no frontend calculation or
unsafe raw-dictionary fallback was introduced. The smallest safe remediation is an
explicitly authorized Prompt-13 frontend foundation stage that creates typed Feature-54
Graph/Claim/Disagreement ViewModels, isolated current/historical State, exact snapshot
routing, an accessible topology renderer, and its real-browser harness.

## D3 preflight: historical disagreement linkage blocker (2026-08-15)

D1 and D2 remain valid: production Claim producers emit independently attributable
`BITCOIN_NETWORK` Claims, and the backend evaluator deterministically distinguishes
agreement, disagreement, insufficient coverage, and non-comparability. D3 cannot yet
truthfully expose the required historical request-to-DOM contract because its stated
snapshot and privacy prerequisites are not present in repository truth.

| Required authority | Current implementation | Exact gap | Smallest safe remediation |
| --- | --- | --- | --- |
| Persisted immutable Graph Snapshot | `BitcoinTopologyPipeline.history_for_events` rebuilds prefix snapshots from the currently loaded `OnchainEvent` rows; `TraceGraphApiProjectionService` then derives Graph/snapshot IDs from those in-memory projections | No Graph Snapshot model, migration, repository, immutable payload, or restart-stable exact-read operation exists | Add append-only Graph Snapshot persistence with a strict versioned payload, source Topology Snapshot linkage, idempotent semantic key, and exact Trace/snapshot read |
| Historical disagreement correlation | `TraceHistoricalDisagreementService` groups immutable Claims by `report_id` and evaluates them, while Graph history entries have no persisted capture row | A report capture cannot be associated with an exact immutable Graph Snapshot identity without timestamp approximation or current-state substitution | Persist a typed Graph Snapshot → Claim capture/evaluation-boundary reference and pin producer/evaluator versions |
| Browser privacy authority | Existing Trace evidence governance provides endpoint-specific evidence access decisions, not a centralized Trace Graph/Claim/Disagreement field policy | There is no default-deny classification/projection authority from which a strict safe Claim or Disagreement DTO can be derived | Establish a centralized backend Trace Privacy Policy with explicit ALLOW/DENY/REDACT mappings and unknown-field DENY before adding the D3 API |

The current Graph routes expose only a projection of the current snapshot and a
transient history index. There is no operation accepting `(report_id, snapshot_id)`
and returning that exact persisted snapshot. Consequently, adding a historical
disagreement route now would necessarily fetch report-current Claims, approximate by
time, or imply persistence that does not exist; each is explicitly forbidden.

This is the D3-specific strict stop condition:

`D3_HISTORICAL_DISAGREEMENT_LINKAGE_MISSING — D2 historical results are scoped to a
report Claim capture, but no persisted immutable Graph Snapshot identity/state exists
to bind that capture to an exact historical Graph; centralized default-deny Trace
privacy projection authority is also absent.`

Affected gates include D3-A06–A13, D3-A24–A31, D3-A44–A46, D3-A74–A90, and the
original Prompt-13 immutable-history/privacy gates. D1/D2, T1–T4, and current Graph
projection are not reopened. No API, generated transport, State, or UI was added:
making disagreement unavailable is safer than introducing current-state fallback,
frontend evaluation, or an unreviewed privacy allowlist.

Independent rollback is documentation-only: remove this D3 preflight section. Such a
rollback must not add a disagreement endpoint, reconstruct historical state, or expose
internal Claim fields. The durable remediation can be rolled back independently by
disabling exact history selection while retaining stored immutable snapshots and by
keeping the privacy projection default-deny; it must never fall back to current Graph
or restore denied fields.

> **D2 supersession:** the internal typed Disagreement Domain now evaluates the
> D1 `BITCOIN_NETWORK` Claim pair as agreement, disagreement, insufficient, or
> not comparable. Resolution remains explicitly unavailable (R1). D3 still owns
> privacy-safe API and Prompt-13 integration.

> **D1 supersession:** `DISAGREEMENT_COMPARABLE_CLAIM_SOURCE_MISSING` is closed by
> the production Claim foundation documented in `TRACE_CLAIM_FOUNDATION.md`.
> Address syntax and T1 observation-source metadata now independently produce
> attributable `BITCOIN_NETWORK` Claims for the same Bitcoin-address subject.
> Disagreement evaluation remains intentionally deferred to D2.

## Prompt-13R3 comparable-claim producer audit (2026-08-15)

Prompt-13R3 explicitly authorized new snapshot persistence, a Claim/Disagreement
Domain, and a centralized privacy policy. Before creating those models, the required
producer inventory found a deeper strict-stop condition: current production Trace
analysis never emits multiple comparable authoritative claims.

### Producer inventory result

| Candidate output | Comparable claims? | Classification | Reason |
| --- | --- | --- | --- |
| Baseline Trace score/band | No | `SINGLE_METHOD_OUTPUT` | One deterministic baseline scorer emits one band for one report |
| Risk source registry | No | `SOURCE_CONFIGURATION_ONLY` | Registry rows describe configured sources; they do not carry source-specific claims |
| Bitcoin observations | No | `SAME_FACT_OBSERVATIONS` | T1 emits factual address/transaction observations, not competing classifications |
| Bitcoin topology relationship | No | `SINGLE_AUTHORITATIVE_RELATIONSHIP` | T2 emits one reproducible relation from observations; no producer disputes it |
| Provider operational availability | No | `OPERATIONAL_PROVIDER_FAILURE` | Failure/missingness is explicitly not analytical disagreement |
| Existing disagreement call | No | `PLACEHOLDER_SINGLE_VALUE` | Production passes one hard-coded `"unknown"` origin and one baseline risk band |

`TraceService.analyze_address` calls `detect_disagreement(["unknown"],
[scoring.band.value])`. There is no provider claim producer before this call and no
second comparable value. `ProviderDisagreementService` can compare caller-supplied
string arrays in isolation, but production never supplies source-associated claims.
Its conflict branches are therefore utility behavior, not an authoritative current
analytical disagreement source.

The exact Prompt-13R3 stop code is:

`DISAGREEMENT_COMPARABLE_CLAIM_SOURCE_MISSING — production Trace emits one baseline
risk-band result and one hard-coded unknown origin label; no current producer emits
multiple source-associated claims for the same typed subject and predicate.`

Creating Claim records from the existing string-list helper would invent claim IDs,
subjects, source association, observation times, provenance, and historical capture
membership. Creating synthetic conflicting claims solely for API/UI acceptance would
violate the no-fabrication rule.

### Smallest safe remediation

Add an analytical producer that obtains at least two genuinely comparable,
source-associated claims for a supported current predicate (for example, the existing
risk-band or origin-category predicate), with stable subject, source identity,
evaluation time, provenance, confidence where owned, and limitations. That producer
must feed the Claim/Disagreement Domain at report/snapshot creation time. Provider
failure and missing data must remain separate states.

Snapshot persistence and privacy policy can be built independently, but completing
them cannot satisfy Prompt-13R3-A20 through A35, the typed disagreement UI, or the
mandatory producer→DOM lineage. Because the final acceptance requires all applicable
Prompt-13 features in this same run, partial persistence/privacy work would leave the
same non-resumable UI state and was not introduced speculatively.

T1-T4 current topology, the real non-report Bitcoin relationship, Graph projection,
current typed Graph API, and Prompt-12 remain regression-green. The old topology
producer blocker remains closed.

---

## Prompt-13R2 persistence and producer audit (2026-08-15)

Prompt-13R2 authorized implementation of exact historical reads, typed disagreement,
and browser-safe privacy projection. Preflight found that each missing transport
contract is blocked by a deeper upstream authority gap rather than serializer work.
No frontend or API contract was added.

| Gap | Current producer/storage | Current API | Deeper missing boundary | Required authority |
| --- | --- | --- | --- | --- |
| Exact historical Graph read | History is recomputed from mutable `OnchainEvent` rows; no Topology or Graph snapshot model/table stores immutable payloads | History index and current snapshot reads | History IDs identify ephemeral rebuild results, not persisted immutable Graph state | Canonical immutable snapshot repository/model and migration storing safe content or immutable source references |
| Disagreement | Producer receives parallel `list[str]` values and returns aggregate conflict metadata; persistence stores `model_dump()` JSON | Generic `dict[str, object]` | Producer discards claim-to-provider association and owns no typed alternatives, observed times, stable subjects, or canonical resolution | Upstream typed claim observations and a producer that retains claim/source identity |
| Privacy safe projection | `PrivacyShieldReport` is persisted as generic JSON | Generic `dict[str, object]` | No repository policy classifies Graph, disagreement, provenance, or privacy fields as browser-safe/internal/redactable | Product-owned field classification and versioned default-deny safe projection policy |

### Exact historical persistence evidence

`BitcoinTopologyPipeline.history_for_events` deterministically rebuilds every
history prefix in memory. `TraceGraphApiProjectionService.history_for_report_model`
then derives IDs from those transient Graph hashes. No database model, repository,
or migration persists a Topology Snapshot, Graph Snapshot, immutable payload, or
immutable source-reference set. Because `OnchainEvent` rows include mutable fields,
an exact read implemented today would rerun T1-T4 against today's rows and could
return different content under the same conceptual historical position.

The exact stop code is:

`FEATURE26_IMMUTABLE_GRAPH_PAYLOAD_NOT_PERSISTED — history IDs are transient
content-derived projections; persistence stores neither immutable Graph payloads
nor immutable source references sufficient for an exact selected-snapshot read.`

Smallest safe remediation: introduce a canonical append-only snapshot persistence
model through the repository migration mechanism. It must correlate report ID,
Graph snapshot ID, Topology snapshot ID, capture time, versions, integrity digest,
and either a strict immutable safe Graph payload or immutable source references
whose reconstruction semantics are explicitly versioned. History indexing and
exact reads must query that repository rather than rebuild all prefixes.

### Disagreement producer evidence

`ProviderDisagreementService.detect_disagreement` receives only origin-label and
risk-band string lists. It can detect aggregate conflict, but it has no claim ID,
provider-to-claim mapping, observed time, stable Graph subject, or resolved claim.
The first semantic loss occurs before persistence/API serialization. Wrapping the
existing aggregate in new alternative DTOs would fabricate provider attribution
and claim semantics.

The exact stop code is:

`TRACE_DISAGREEMENT_PRODUCER_SEMANTICS_INCOMPLETE — the producer owns aggregate
conflict metadata only and receives no typed source-associated claim alternatives.`

Smallest safe remediation: define typed source claims at the analytical producer
input, preserve those claims in the disagreement result and persistence model,
and only then project an explicit browser-safe disagreement DTO. Resolution must
remain absent unless a backend producer genuinely owns it.

### Privacy policy evidence

The repository has privacy helper output but no authoritative cross-domain policy
classifying Graph nodes, relationships, observation references, provenance,
disagreement claims, and privacy fields into browser-safe, internal-only, secret,
or redactable categories. Creating an allowlist without that product authority
would silently decide security semantics in this implementation prompt.

The exact stop code is:

`TRACE_PRIVACY_POLICY_AUTHORITY_MISSING — no canonical field-classification policy
defines which Trace Graph, historical, disagreement, provenance, and privacy fields
may cross the browser boundary.`

Smallest safe remediation: establish a versioned backend privacy policy and tests
for every exposed field, then implement an explicit constructor-based allowlist.
Unknown fields must remain denied, original redacted values must never enter the
DTO, and synthetic canaries must be absent at HTTP serialization.

Because these are valid Prompt-13R2 stop conditions, implementing routes, generated
contracts, Feature-54 adapters, State, or browser UI now would require fabricating
immutable persistence, disagreement claim semantics, or privacy policy. The T1-T4
current-topology chain remains healthy and is not reopened.

---

Status: **BLOCKED ON RETRY — T1-T4 topology authority is present, but the current
transport does not provide a selectable historical Graph capture and the advanced
disagreement/privacy endpoints remain type-erased.**

## Prompt-13 retry preflight (2026-08-15)

The T1-T4 regression chain now passes and produces the real, directed, non-report
`ADDRESS_PARTICIPATES_IN_TRANSACTION` relationship through Observation,
Relationship, Topology Snapshot, Graph Snapshot, and the typed current Graph API.
The old `FEATURE23_ANALYTICAL_RELATIONSHIP_SOURCE_MISSING` blocker is therefore
closed and must not be reused.

UI implementation still cannot begin truthfully because three independently
required read boundaries are incomplete:

1. `GET /trace/report/{report_id}/graph/history` returns typed history metadata,
   but there is no operation that accepts a stable topology/Graph snapshot ID and
   returns that exact historical Graph. The current snapshot endpoint always
   rebuilds the latest topology from all matching `OnchainEvent` rows. A browser
   cannot deep-link, refresh, or render capture A after capture B without either
   reconstructing history or silently loading current data.
2. `GET /trace/report/{report_id}/provider-disagreement` still declares a generic
   dictionary response and does not expose typed alternatives, provider identity,
   observation time, or an authoritative resolution. A frontend adapter would
   have to interpret arbitrary keys or manufacture the comparison model.
3. `GET /trace/report/{report_id}/privacy-shield` still declares a generic
   dictionary response. There is no versioned browser-safe allowlist DTO carrying
   redaction posture and allowed actions, so absence of internal fields cannot be
   proven by construction through generated transport, State, and DOM.

Feature 25 also remains not applicable to animation: current topology node DTOs
do not own per-node freshness. Prompt 13 may render nodes statically, but must not
reuse report freshness as node freshness or claim the canonical node-pulse feature.

The retry stop code is:

`FEATURE26_HISTORICAL_CAPTURE_READ_REGRESSION — history lists snapshot identities,
but no typed operation can retrieve the exact immutable Graph for a selected
snapshot; disagreement and privacy safe-read contracts are also not UI-ready.`

### Recovered feature status

| Feature | Canonical name | Backend authority now available | Prompt-13 UI responsibility | Retry disposition |
| --- | --- | --- | --- | --- |
| 23 | Graph focus, pin and isolate | Current typed Graph contains authoritative Bitcoin address/transaction nodes and directed non-report relationships | Presentation-only focus, pin, isolate, inspectors, and accessible equivalent | `READY_AFTER_SHARED_BLOCKERS` |
| 24 | Semantic graph edge types | Typed Graph relationship identity, source, target, direction, taxonomy, provenance, and limitations | Render exact backend semantics; never merge or strengthen edges | `READY_AFTER_SHARED_BLOCKERS` |
| 25 | Node pulse driven by freshness | No per-node freshness authority | Static node rendering only; pulse is not applicable | `NOT_APPLICABLE_UNTIL_NODE_FRESHNESS_EXISTS` |
| 26 | Graph time travel | Typed history index and snapshot correlation exist, but selected capture retrieval does not | Deep-link and render an exact immutable selected capture | `BLOCKED_MISSING_CAPTURE_READ_OPERATION` |

### Retry authority matrix

| UI concept | Current operation | DTO authority | Frontend-safe status |
| --- | --- | --- | --- |
| Current node/edge topology | Graph snapshot/object/relationship reads | Strict generated Graph DTOs | Ready |
| Historical index | Graph history read | Strict history entries | Ready as an index only |
| Selected historical topology | None | None | Blocked; frontend reconstruction forbidden |
| Disagreement | Provider-disagreement read | `dict[str, object]` | Blocked by type erasure |
| Privacy | Privacy-shield read | `dict[str, object]` | Blocked; no default-deny browser DTO |

No topology route, Reflex State, renderer, fixtures, or browser evidence is added
by this retry audit. That preserves semantic-inference, historical-reconstruction,
disagreement-calculation, and browser-private-field counts at zero.

---

The material below records the original pre-T1 audit and is retained as historical
context. Its Feature-23 topology-source conclusion is superseded by the retry
preflight above.

Status at original audit: **BLOCKED — authority was insufficient for an
implementation that did not invent forensic meaning in the browser.**

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
