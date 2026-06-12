# Event Integration Gaps

Bitcoin Bastion now publishes several real domain events into the internal Event Outbox only. This gap list is intentionally conservative: events are not fabricated when a stable trigger, registry entry, or durable service boundary does not exist yet.

External webhook delivery, WebSocket streaming, SDK consumption, CLI commands, MCP connectors, and plugin execution are not implemented by this prompt.

| Event type | Expected trigger | Why it was not wired yet | Likely future file/service | Blocking dependency |
| --- | --- | --- | --- | --- |
| `news.article.scored` | Article score persisted after BTC/news scoring | The current scoring path returns in-memory score output and does not expose one durable article-score persistence hook. | `app/services/intelligence/news_scorer.py`, `app/services/intelligence/news_ingestion/` | Stable persisted score lifecycle and idempotency key. |
| `news.event.created` | Durable market/news event cluster creation | Event clustering is not a single stable service boundary in the current ingestion flow. | `app/services/intelligence/news_ingestion/`, `app/services/intelligence/event_*` | Canonical event-cluster creation service. |
| `news.event.high_impact` | High-impact event detection after scoring | High-impact detection is not currently emitted as a durable state transition. | `app/services/intelligence/news_price_impact*` | Durable high-impact state transition and threshold contract. |
| `market.regime.changed` | Market regime state transition | Market regime generation does not currently persist a previous/current regime transition. | `app/services/market*`, `app/services/intelligence/market_*` | Regime state store and transition semantics. |
| `market.price_tick.observed` | Durable provider price tick ingestion | Price tick observation is provider/runtime oriented and not yet a canonical domain persistence hook. | `app/services/market_data/`, `app/tasks/` | Durable tick table or event source. |
| `market.candle.closed` | Candle close persisted | Candle close lifecycle is not separated from existing candle data access paths. | `app/services/market_data/`, candle repositories | Canonical candle close hook. |
| `trace.risk_band.changed` | Existing report changes from one trace band to another | Trace analysis currently creates fresh baseline reports and does not track previous band transitions. | `app/services/bastion_trace/trace_service.py` | Previous-band comparison and update workflow. |
| `trace.source_disagreement.detected` | Provider disagreement moves above a review threshold | Disagreement metadata exists, but there is no durable threshold transition hook. | `app/services/bastion_trace/provider_disagreement.py` | Threshold contract and idempotency key. |
| `wallet.privacy_risk.high` for all wallet sources | Wallet privacy health reaches a high-risk band | The event is wired for health report generation only; no broader wallet runtime source exists. | `app/db/repositories/wallet_repository.py`, wallet services | Stable wallet-health generation source for every profile. |
| `treasury.policy.failed` for all policy failures | Treasury policy denies or blocks a request | The event is wired for treasury service decisions, but not every future treasury policy path is centralized yet. | `app/services/treasury/treasury_service.py` | Centralize all treasury policy decisions through the current service. |
| `evidence.replay.failed` for every replay failure | Replay execution fails after durable replay log creation | Failure events are wired in the current replay service, but future replay surfaces must reuse that service. | `app/services/intelligence/evidence_replay_service.py` | Route all replay workers through the service. |
| `provider.stale` | Provider data age exceeds stale threshold | This event type is not in the current canonical registry and no stale-data lifecycle hook exists. | `app/services/market_data/provider_health.py` | Taxonomy expansion and stale threshold contract. |
| `provider.confidence.changed` | Provider confidence crosses a configured threshold | This event type is not in the current canonical registry; provider health currently emits degradation/recovery transitions. | `app/services/market_data/provider_health.py` | Taxonomy expansion and confidence transition contract. |
| `job.completed` | Background job finishes successfully | This event type is not in the current canonical registry and jobs are not centralized behind an event-aware runner. | `app/tasks/`, observability services | Taxonomy expansion and job wrapper. |
| `runtime.degraded` | Runtime enters degraded state | Current registry uses `system.degraded_mode.entered` / `system.degraded_mode.exited`; route-level runtime state is not centralized. | `app/core/telemetry.py`, runtime status services | Decide whether to use existing system events or expand taxonomy. |
| `market.narrative.spiked` | Narrative heatmap/spike crosses threshold | This event type is not in the current canonical registry and no stable narrative spike transition hook exists. | `app/services/intelligence/`, market narrative services | Taxonomy expansion and narrative spike state store. |
| `market.historical_similarity.generated` | Historical similarity output is generated | This event type is not in the current canonical registry and similarity outputs are informational, not persisted as a durable event yet. | `app/services/intelligence/`, Market Time Machine services | Taxonomy expansion and durable similarity output. |
| `trace.business_batch.completed` | Business-specific Trace batch completes | Current canonical registry has `trace.batch.completed`; no separate business-specific event type exists yet. | `app/services/bastion_trace/trace_service.py` | Taxonomy expansion if separate business semantics are required. |
| `evidence.artifact.created` | Individual evidence artifact is persisted | Current canonical registry has `evidence.packet.created`; per-artifact publication would add noisy rows and needs explicit taxonomy. | `app/services/intelligence/evidence_packet_builder.py` | Taxonomy expansion and artifact-level delivery policy. |

## Current wired baseline

- Signals: candidate creation, operator review required, publication, and suppression are wired.
- Trace: report creation, batch completion, and treasury destination checks are wired.
- Treasury: request creation, approval requirement, approval, rejection, and policy failure paths are wired where the treasury service owns the workflow.
- Evidence: packet creation and replay completion/failure are wired through the evidence services.
- Provider health: degradation and recovery are wired.
- On-chain: registered large transfer, watchlist hit, fee spike, and mempool pressure event types are wired when ingestion receives those public chain events.
- Wallet: health generation and high privacy-risk health reports are wired.
- Policy: evaluation completed, warning created, and execution failed events are wired through the treasury policy service.

All current domain events are internal/outbox-only and must not be interpreted as proof of payment, legal status, Bitcoin consensus proof, trading correctness, or production delivery evidence.
