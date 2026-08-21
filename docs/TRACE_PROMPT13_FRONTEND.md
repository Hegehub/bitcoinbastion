# Prompt-13 Trace topology/history frontend foundation

## Ownership matrix

| Backend authority | Operation | Generated DTO | Feature-54 VM | Reflex State | Route | Component |
| --- | --- | --- | --- | --- | --- | --- |
| Persisted history index | `get_trace_graph_history…` | `TraceGraphHistoryDTO` | `TraceHistoryIndexItemViewModel` | `TraceTopologyState.history` | `/trace/[report_id]` | immutable history list |
| Current topology | history latest ID + `get_exact_trace_graph_snapshot` | `TraceGraphDTO` | `TraceTopologyViewModel` | `TraceTopologyState.topology` | `/trace/[report_id]` | topology renderer and structured lists |
| Exact historical Graph | `get_exact_trace_graph_snapshot` | `TraceGraphDTO` | `TraceTopologyViewModel` | `TraceHistoryState.topology` | `/trace/[report_id]/history/[snapshot_id]` | historical topology |
| Current D2 result | `get_current_trace_disagreement` | `SafeTraceDisagreementCollectionDTO` | `TraceDisagreementCollectionViewModel` | `TraceTopologyState.disagreement` | `/trace/[report_id]` | analytical status cards |
| Historical D2 result | `get_historical_trace_disagreement` | `SafeTraceDisagreementCollectionDTO` | `TraceDisagreementCollectionViewModel` | `TraceHistoryState.disagreement` | exact history route | historical analytical status cards |
| Nodes/relationships | exact Graph response | strict Graph object/relationship DTOs | typed node/relationship VMs | selected typed VM only | both routes | visual cards, structured lists, inspectors |
| Provenance/limitations | strict safe nested DTOs | strict provenance fields | safe labels/limitations | typed VM fields | both routes | visible status and limitation copy |
| Privacy/redaction | backend policy projection | safe DTO fields only | default-deny adapter fields | no raw transport/dict | both routes | safe values only; no raw/debug control |

Frontend analytical ownership is **NONE**. Generated transport ends at the
Feature-54 adapter. Components import only ViewModels and State.

## Renderer and lifecycle

The renderer uses existing Reflex/Radix primitives and adds no graph dependency. It
renders each authoritative node and each distinct directed backend relationship as an
interactive card; it never merges multi-edges. Coordinates are not required and no
layout state enters the domain. The same ViewModel drives the visual region and the
structured keyboard-accessible node/relationship representation, so zoom or pointer
interaction is not required to access information.

Current State loads the bounded history index, then requests only the latest exact
snapshot and current D2 status. Historical State is separate and accepts the persistent
snapshot ID from the canonical route. Both use generation tokens; route exit increments
the token, and late results cannot commit. Historical failure remains unavailable and
never invokes current Graph or Trace Submit. Selection and theme changes are local
presentation state and do not issue domain requests.

Feature-52 remains exactly LIVE, VERIFIED_SNAPSHOT, DEMO_FIXTURE, and UNAVAILABLE.
Historical mode is a domain mode and remains LIVE unless separate verification
authority says otherwise. Feature-59/60 development scenarios are typed and explicitly
DEMO_FIXTURE; production State has no fixture fallback.

## Request-to-render lineage

- T1→T4 relationship → persisted Graph → exact operation → generated DTO → typed
  relationship VM → State → visual edge card and structured relationship DOM.
- History index → persistent snapshot ID → exact operation → typed historical VM →
  isolated historical State → Historical Trace DOM.
- D2 result → safe operation → typed Claim/Disagreement VMs → State → status and
  producer-attributed Claim DOM. The adapter preserves status; it never compares values.
- Internal privacy canary → backend DENY → absent safe DTO → absent VM, State, DOM, and
  accessibility metadata.

## Browser evidence (2026-08-15)

The repository-supported Reflex server, FastAPI server, Playwright 1.62 Chromium 151,
and Playwright's supported `install-deps chromium` setup executed successfully.
Canonical services created report 1 and two T1→T4 relationships; no Graph edge was
inserted directly.

- Current route rendered 5 nodes, 3 directed relationships, two persistent history
  identities, D2 insufficient/not-comparable states, and the real
  `address_participates_in_transaction` relationship.
- A/B/A used snapshot IDs `trace_snapshot:85323e6add2b831ac6997af1` and
  `trace_snapshot:aa3bcb118519d6c0f4136b0b`. A rendered one topology relationship;
  B rendered two; Back and Refresh restored A with no B-only relationship.
- Backend logs showed one history, one exact Graph, and one current disagreement read
  for the current logical load; each historical navigation issued one exact Graph and
  one exact historical disagreement read. No Trace Submit mutation occurred.
- Keyboard Enter on a focused node opened the node inspector. Narrow viewport width
  390 produced document width 390. Dark + reduced-motion current and light +
  reduced-motion historical runs completed.
- Canary occurrences were zero in page text and ARIA/title/data attribute searches.

Screenshots were used as transient verification only and are not committed.

## Rollback

ViewModels, current State, historical State, renderer, lists, inspectors, history route,
disagreement cards, route lifecycle wiring, scenarios, tests, and docs can be removed
independently. Rollback must make topology/history unavailable. It must not fetch
current Graph for history, compare Claims in the frontend, expose raw DTOs, or remove
backend snapshots/privacy/D1/D2/T1–T4/G1–G4 authority.
