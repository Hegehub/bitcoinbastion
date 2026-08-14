# Prompt 10 typed historical Market matrix

## Authority-gap resolution

| Domain | Producer/store | Former erasure | Canonical owner now |
|---|---|---|---|
| Timeline item/order/time/source | `TimelineService` / `intelligence_timeline_events` | API `dict[str, object]` and generated dictionary root | `MarketHistoryService` → `MarketTimelineEventOut` / `MarketTimelinePageOut` |
| Replay capture/version/integrity | persisted Timeline event | arbitrary replay dictionaries | content-addressed `MarketReplayCaptureOut`; schema version `market-replay.capture.v1`; SHA-256 canonical-event digest |
| Attribution | candle attribution engine / `candle_attributions` | explanation, limitations and links as dictionaries | `MarketAttributionOut` with conservative relationship enum and bounded safe text |
| Narrative | `market_narratives` | dictionary-root narrative APIs | plain-text `MarketNarrativeOut` with `STORED_BACKEND_RECORD` origin |
| Source | `news_sources` | internal record/generic dictionary | allow-listed `BrowserSafeMarketSourceOut` |
| Evidence link | `evidence_packets` plus Evidence integrity snapshots | generic relationship dictionaries | `MarketEvidenceLink`; link relation and integrity-record availability remain separate from verification |

Legacy generic APIs and JSON fields remain available to their existing owners but are not
consumed by the Prompt-10 frontend. Unknown producer event types map through the backend to
`OTHER`; raw payloads remain server-side. No legacy record is mutated or guessed during this
read-only compatibility projection.

## Semantic ownership

Timeline order is `occurred_at DESC, event_id DESC`; equal event times use durable ID as the
tie-breaker. `occurred_at` is producer event time and `observed_at` is persisted ingestion
time. Event kind is a backend projection; `producer_type` preserves the bounded original
label. Frontend transformations are formatting and bounded rendering only.

Replay capture identity is UUIDv5 over the SHA-256 digest of canonical JSON serialization of
the typed event. The schema version describes the capture wire meaning. The same semantic
event produces the same digest and capture ID; changed content produces a new identity. The
digest means **content equality only**—not external truth, causality, Feature-52 verification,
or Evidence verification. Current Market State and replay State are distinct.

Attribution supports `ASSOCIATED` and `CORRELATION_CANDIDATE`. Neither means causal. Backend
confidence is a ratio and frontend does not normalize it. Strength is omitted because the
producer does not own a distinct strength semantic. Narratives are bounded plain text, not
HTML/Markdown, and use explicit stored-record origin. Sources expose only ID, display name,
type, category, safe homepage, observed time, and limitations. HTTP/HTTPS URLs with embedded
credentials and all other schemes are rejected from the browser DTO.

| Evidence concept | Owner |
|---|---|
| Market→Evidence link | Market history backend relationship projection |
| Evidence verification | Evidence domain; not inferred here |
| Feature-52 provenance | provenance system |
| capture digest | replay content-equality authority |

Counters: `frontend_historical_semantic_inference_count = 0`;
`frontend_replay_recomputation_count = 0`; `frontend_attribution_inference_count = 0`;
`frontend_causal_inference_count = 0`; `frontend_narrative_generation_count = 0`.

## Request-to-render coverage

| Surface | Operation | Generated DTO | Adapter / State | Named DOM evidence | Coverage |
|---|---|---|---|---|---|
| Timeline | `market_history_timeline` | `MarketTimelinePageOut` | `adapt_timeline` / `MarketHistoryState` | title, kind, producer type, event/observed times, source, summary, limitations | IMPLEMENTED_VERIFIED |
| Replay | `market_history_replay_event` | `MarketReplayCaptureOut` | `adapt_replay` / isolated `replay` | capture ID, version, effective/captured time, digest meaning, historical event | IMPLEMENTED_VERIFIED |
| Attribution | `market_history_attributions` | `MarketAttributionOut[]` | `adapt_attributions` | relation text, confidence, explanation, limitations | IMPLEMENTED_VERIFIED |
| Narratives | `market_history_narratives` | `MarketNarrativeOut[]` | `adapt_narratives` | title, plain body, origin, time, confidence, limitations | IMPLEMENTED_VERIFIED |
| Sources | `market_history_sources` | `BrowserSafeMarketSourceOut[]` | `adapt_sources` | source ID/name/type/category/safe URL/time/limitations | IMPLEMENTED_VERIFIED |
| Evidence references | embedded typed links | `MarketEvidenceLink[]` | nested safe adapter | label, relationship, explicitly non-verification status | IMPLEMENTED_VERIFIED |

Chromium 145 real-stack evidence exercised all five HTTP operations, typed seeded backend
records, replay interaction, Evidence reference rendering, and 390×844 overflow. No browser
profile, screenshot, storage state, private key, or authentication material is retained.

## Feature 59/60

Lifecycle supports empty, unavailable/error, missing replay (404), and partial optional
metadata. Backend tests cover unsafe URL rejection and deterministic replay. Feature-60 uses
generated typed schemas, fixed IDs/times, and `DEMO_FIXTURE`; production State never imports
or falls back to it.

## Lineage

* Timeline: persisted `IntelligenceTimelineEvent` → `MarketHistoryService.event` →
  `market_history_timeline` → generated `MarketTimelineEventOut` → `adapt_timeline` →
  `MarketHistoryState.timeline_items` → `.market-timeline-item`.
* Replay: persisted event → canonical JSON/SHA-256/UUIDv5 → `MarketReplayCaptureOut` →
  generated client → `adapt_replay` → isolated replay State → `#replay-capture-id`.
* Attribution: `CandleAttribution` → conservative backend taxonomy → typed API/DTO → adapter
  → State → relationship text.
* Narrative: `MarketNarrative.description` → bounded plain-text DTO → adapter → State →
  paragraph DOM (never raw HTML).
* Source: internal `NewsSource` → backend allow-list and URL validation → safe DTO → adapter
  → State → labeled metadata/safe anchor.
* Evidence: `EvidencePacket` plus optional integrity record → typed link → adapter → DOM;
  integrity availability is never promoted to verification.

## Rollback

Remove the `/market/history` router/service/schemas, generated operation family, Prompt-10
adapters/State/screens/routes and typed fixtures. This preserves the legacy historical stores,
Prompt-9 Market Overview/Signals, Feature 52/54/67, Stage-4 WS, canonical shell/topology, and
all user data. Rollback must not restore raw JSON rendering.
