# Prompt 10 historical Market authority audit

Status: **RESOLVED by the typed authority described in `10_TYPED_HISTORICAL_MARKET_MATRIX.md`.**

## Canonical feature recovery

| Feature | Canonical name | Current state | Prompt-10 consumer | Required evidence |
|---|---|---|---|---|
| 13 | Synchronized chart crosshair | Not verified | Timeline/chart | Typed observations, synchronized named values, DOM and accessible table evidence |
| 14 | Replayable time scrubber | Not verified | Replay | Stable capture/version identity and deterministic typed replay response |
| 15 | Collision-aware event markers | Not verified | Timeline | Typed event identity/order/time and backend duplicate/collision semantics |
| 16 | Attribution waterfall | Not verified | Attribution | Backend relationship taxonomy, typed candidates, confidence and limitations |
| 17 | Narrative heatmap | Not verified | Narratives | Typed backend-authored narrative snapshots with origin and limitations |
| 19 | Zoom and brush lens | Not verified | Timeline/replay | Backend-bounded time window and accessible equivalent |
| 21 | Provider freshness overlay | Not verified | Sources | Typed historical provider observation and freshness semantics |
| 22 | Direct labels and contextual annotations | Not verified | Timeline/attribution | Backend-owned labels/annotations and textual accessible equivalents |

The feature register states that every item is Prompt-10-owned and still requires named
fields, failure states, contract evidence, and browser DOM/accessibility evidence.

## Candidate ownership inventory

| Classification | Operation / store | Current contract | Authority finding |
|---|---|---|---|
| REQUIRED, contract-blocked | `get_timeline_api_v1_intelligence_timeline_get` / `intelligence_timeline_events` | `RootModel[dict[str, JsonValue]]` | Durable event identity and event/ingestion times exist, but the API erases them into an unconstrained dictionary and omits `ingested_at`, `source_kind`, and a canonical sequence |
| REQUIRED, contract-blocked | `market_events_api_v1_market_time_machine_events_get` | `MarketTimeMachineAnalyticsResponse.items: list[dict[str, Any]]` | Bounded historical query exists, but item type is erased and `payload_json` admits an opaque provider payload |
| REQUIRED, authority-blocked | candle/event replay operations | `RootModel[dict[str, JsonValue]]` | No strict replay DTO exposes stable snapshot/capture version, source revision, integrity state, and deterministic historical Market state |
| REQUIRED, contract-blocked | candle attribution operations / `candle_attributions` | generic dictionaries and JSON fields | Stored candidates exist, but relation taxonomy, evidence references, explanations, and limitations cross the API as untyped dictionaries |
| REQUIRED, contract-blocked | narrative operations / narrative snapshot tables | `RootModel[dict[str, JsonValue]]` | Backend records exist, but safe authored text/origin/model identity, limitations, and source references are not a strict browser contract |
| REQUIRED, contract-blocked | news source operations / `news_sources` | mostly `RootModel[dict[str, JsonValue]]` | Stable source records exist, but safe metadata and external URL allow-list fields are not separated from arbitrary payloads |
| OPTIONAL, contract-blocked | Evidence replay/link operations | `RootModel[dict[str, JsonValue]]` | Evidence identities exist, but Market-safe reference and verification semantics are not typed; Prompt 10 cannot safely project them |
| FUTURE | historical similarity operations | generated operations exist | Prompt 11 ownership; deliberately not consumed |

Feature-53 identities and exactly-one generated clients exist for many candidates. That does
not make their unconstrained response dictionaries safe Feature-54 inputs.

## Historical-authority audit

### Timeline

`intelligence_timeline_events` supplies a durable integer identity, `event_time`,
`ingested_at`, related object IDs, and limitations. The current API projection drops source
kind and ingestion time and has neither a typed sequence/cursor nor an explicit duplicate
relationship. The alternative analytics endpoint returns heterogeneous dictionary items.
Consequently event-vs-observation time, ordering, pagination, collision behavior, and safe
source projection cannot be proven through generated DTOs.

### Replay

Evidence, candle-context, attribution-context, narrative, and Market-memory snapshot tables
are historical candidates. Current replay endpoints return arbitrary dictionaries and do not
provide one canonical Market replay envelope containing a stable replay/capture ID, schema
version, capture time, source revision, integrity result, historical measurements, and
historical signal/provider state. `replay_available` booleans are capability hints, not replay
authority. A live request to these endpoints cannot truthfully be projected as
`VERIFIED_SNAPSHOT`.

### Attribution

`candle_attributions` persists backend scores, relationship labels, candidates, evidence
references, explanations, and limitations. Several of those fields remain JSON dictionaries,
and public operations expose dictionary roots. The frontend therefore cannot distinguish an
authoritative relation type from explanatory metadata without interpreting raw payloads.

### Narratives

Market narrative and snapshot storage exists. The current narrative endpoints return
dictionary roots and do not define a safe narrative body/origin contract, sanitization mode,
safe links, hidden-model-metadata exclusion, or typed limitation/source references. Reflex
must not generate or reinterpret narrative prose to fill those gaps.

### Sources and Evidence links

News/source and Evidence stores provide stable database identities. Most source/detail and
Evidence replay endpoints still expose generic dictionaries. No strict Market source DTO
defines a safe external URL or an allow-listed metadata projection, and no strict compact
Market Evidence reference distinguishes linkage from verification. Raw projection would risk
provider secrets and false proof semantics.

## Required backend remediation

The smallest safe remediation is to add, without changing stored authority:

1. strict Timeline item/page DTOs containing identity, backend ordering/cursor, event and
   observation times, source identity/type, typed relation references, and limitations;
2. a canonical deterministic Market replay envelope with capture ID, schema/source version,
   capture window, integrity metadata, typed historical state, and explicit not-found/partial
   behavior;
3. strict Attribution subject/candidate/relation/evidence/limitation DTOs with a documented
   backend relationship taxonomy;
4. strict Narrative DTOs defining safe text format, author/origin, timestamps, confidence,
   limitations, and safe reference records;
5. strict Source and compact Market Evidence-reference DTOs that allow-list browser-safe
   metadata and URL schemes;
6. full Stage-1 regeneration after those OpenAPI changes.

Until then the safe counters remain:

`frontend_causal_inference_count = 0`

`frontend_replay_recomputation_count = 0`

`frontend_attribution_inference_count = 0`

`frontend_narrative_generation_count = 0`

No Prompt-10 production route is marked `IMPLEMENTED_VERIFIED`, no fixture is used as a
production fallback, and no browser-session pseudo-history is introduced.

## Rollback

This audit is documentation-only. Reverting it leaves Prompt-9 Market Overview/Signals,
Feature 52/54, Feature 67, Stage-4 WS, topology, shell, generated clients, and all user data
unchanged.
