# Access Protected Endpoints Matrix

Bitcoin Bastion uses Proof-of-Access authorization for protected APIs. Legacy bearer/JWT credentials and raw Access Pass values do not unlock premium endpoints.

## Summary counts

| Category | Count |
| --- | ---: |
| Public | 40 |
| Public but rate-limited | 3 |
| Access required | 172 |
| Plan-gated | 34 |
| Scope-gated | 16 |
| Metric-entitlement-gated | 7 |
| Critical action | 21 |

Total classified endpoints: 293.

## Enforcement rules

- Public endpoints remain reachable without Proof-of-Access.
- Premium/private endpoints require Access session verification, revocation checks, entitlement checks, and Policy Engine decisions.
- Plan-gated endpoints return `upgrade_required` when the session plan is below the required tier.
- Scope-gated endpoints return `scope_required`/policy denial when the required scope is absent.
- Metric-gated endpoints return `metric_not_allowed` or `upgrade_required` based on the metric catalog.
- Critical actions require signed request headers and, for Human Intent protected actions, `X-Bastion-Intent-Signature`.
- `Authorization: Bearer` and raw Access Pass values are rejected as access proof.

## Endpoint matrix

| Endpoint | Classification | Gate |
| --- | --- | --- |
| `POST /api/v1/access/certificates` | Access required | Default Access session for non-public API; product decision may refine |
| `POST /api/v1/access/challenges` | Access required | Default Access session for non-public API; product decision may refine |
| `POST /api/v1/access/lockdown` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/access/me` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/access/me/entitlements` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/access/me/limits` | Access required | Default Access session for non-public API; product decision may refine |
| `POST /api/v1/access/payment-intents` | Public | No Proof-of-Access required |
| `GET /api/v1/access/payment-intents/{payment_intent_id}` | Public | No Proof-of-Access required |
| `POST /api/v1/access/payments/btcpay/webhook` | Public | No Proof-of-Access required |
| `POST /api/v1/access/sessions` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/admin/audit-logs` | Plan-gated | Enterprise Proof-of-Access |
| `GET /api/v1/admin/jobs` | Plan-gated | Enterprise Proof-of-Access |
| `GET /api/v1/admin/jobs/recovery-check` | Plan-gated | Enterprise Proof-of-Access |
| `POST /api/v1/admin/jobs/retry` | Plan-gated | Enterprise Proof-of-Access |
| `GET /api/v1/admin/jobs/runs` | Plan-gated | Enterprise Proof-of-Access |
| `GET /api/v1/admin/status` | Plan-gated | Enterprise Proof-of-Access |
| `POST /api/v1/auth/login` | Public | No Proof-of-Access required |
| `POST /api/v1/auth/register` | Public | No Proof-of-Access required |
| `GET /api/v1/citadel/assessment` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/citadel/dependencies` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/citadel/inheritance` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/citadel/overview` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/citadel/policy-checks` | Access required | Default Access session for non-public API; product decision may refine |
| `POST /api/v1/citadel/recalculate` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/citadel/recovery` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/citadel/repair-plan` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/citadel/simulations` | Access required | Default Access session for non-public API; product decision may refine |
| `POST /api/v1/citadel/simulations` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/education/snippets` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/entities` | Access required | Default Access session for non-public API; product decision may refine |
| `POST /api/v1/entities/provenance/refresh` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/entities/watchlist` | Scope-gated | Explicit scope/role + policy |
| `GET /api/v1/evidence/market-memory/{event_id}` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/evidence/packets` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/evidence/packets/{packet_id}` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/evidence/packets/{packet_id}/relationships` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/evidence/packets/{packet_id}/timeline` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/evidence/replay/{entity_type}/{entity_id}` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/evidence/replay/{entity_type}/{entity_id}/integrity` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/evidence/replay/{entity_type}/{entity_id}/timeline` | Access required | Default Access session for non-public API; product decision may refine |
| `POST /api/v1/fees/recommendation` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/health` | Public | No Proof-of-Access required |
| `GET /api/v1/health/degraded` | Public | No Proof-of-Access required |
| `GET /api/v1/health/jobs` | Public | No Proof-of-Access required |
| `GET /api/v1/health/live` | Public | No Proof-of-Access required |
| `GET /api/v1/health/providers` | Public | No Proof-of-Access required |
| `GET /api/v1/health/ready` | Public | No Proof-of-Access required |
| `GET /api/v1/health/runtime` | Public | No Proof-of-Access required |
| `GET /api/v1/health/system` | Public | No Proof-of-Access required |
| `PATCH /api/v1/intelligence/candles/attributions/{attribution_id}/review` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/candles/{candle_id}` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/candles/{candle_id}/attribution` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/candles/{candle_id}/candidates` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/candles/{candle_id}/context` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/candles/{candle_id}/events` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/candles/{candle_id}/evidence` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/candles/{candle_id}/explain` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/candles/{candle_id}/replay` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/candles/{candle_id}/similar` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/candles/{candle_id}/top-events` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/events/{event_id}/memory` | Access required | Default Access session for non-public API; product decision may refine |
| `POST /api/v1/intelligence/events/{event_id}/memory/operator-review` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/events/{event_id}/memory/replay` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/events/{event_id}/similar` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/events/{event_id}/timeline` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/impact/high-confidence` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/narratives` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/narratives/active` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/narratives/dominance` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/narratives/dominant` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/narratives/emerging` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/narratives/falling` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/narratives/heatmap` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/narratives/history` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/narratives/memory` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/narratives/rising` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/narratives/rotations` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/narratives/top` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/narratives/{slug}` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/patterns` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/patterns/{pattern_id}` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/patterns/{pattern_id}/history` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/patterns/{pattern_id}/occurrences` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/patterns/{pattern_id}/reaction-profile` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/patterns/{pattern_id}/statistics` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/reaction-profile/{event_id}` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/similar-events/{event_id}` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/similarity/articles/{article_id}` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/similarity/candle/{candle_id}` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/similarity/event/{event_id}` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/similarity/events/{event_id}` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/similarity/news/{event_id}` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/similarity/signals/{signal_id}` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/similarity/{event_id}` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/similarity/{event_id}/matches` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/timeline` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/timeline/context/{timeline_event_id}` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/timeline/day` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/timeline/hour` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/timeline/latest` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/timeline/narratives/current` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/timeline/news-impacts/high-confidence` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/timeline/news-impacts/recent` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/intelligence/timeline/window` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/market-time-machine/candle-attribution` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/market-time-machine/events` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/market-time-machine/news-impact` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/market-time-machine/provider-degradation` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/market-time-machine/reaction-windows` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/market-time-machine/regime-transitions` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/market-time-machine/signal-reliability` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/market/btc/candles` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/market/btc/candles/latest` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/market/btc/candles/{candle_id}` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/market/btc/candles/{candle_id}/evidence` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/market/btc/candles/{timeframe}/latest` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/market/btc/context` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/market/btc/price` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/market/btc/price/history` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/market/btc/providers` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/market/btc/providers/health` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/market/health` | Public | No Proof-of-Access required |
| `GET /api/v1/market/providers/health` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/metrics/provider-health/history` | Plan-gated | Business or Enterprise Proof-of-Access |
| `GET /api/v1/metrics/provider-health/latest` | Plan-gated | Business or Enterprise Proof-of-Access |
| `GET /api/v1/metrics/source-health/history` | Plan-gated | Business or Enterprise Proof-of-Access |
| `GET /api/v1/metrics/source-health/latest` | Plan-gated | Business or Enterprise Proof-of-Access |
| `GET /api/v1/metrics/status` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/metrics/usage` | Metric-entitlement-gated | Metric entitlement + policy |
| `GET /api/v1/news/articles/{article_id}/duplicates` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/by-sentiment/{label}` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/clusters` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/clusters/{cluster_id}` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/events` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/events/high-impact` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/events/regulatory` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/events/security` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/events/{event_id}` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/events/{event_id}/articles` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/events/{event_id}/impact` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/events/{event_id}/score` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/high-impact` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/high-relevance` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/latest` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/regulatory` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/security` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/sources` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/sources/categories` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/sources/health` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/sources/reputation` | Access required | Default Access session for non-public API; product decision may refine |
| `POST /api/v1/news/sources/reputation/refresh` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/sources/tiers` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/sources/{source_id}` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/sources/{source_id}/confidence-events` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/sources/{source_id}/health` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/sources/{source_id}/snapshots` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/{article_id}/explanation` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/{article_id}/impact` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/{article_id}/narratives` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/{article_id}/score` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/news/{article_id}/scores` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/observability/snapshot` | Plan-gated | Business or Enterprise Proof-of-Access |
| `GET /api/v1/onchain/events` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/onchain/state` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/operations/drills` | Plan-gated | Business or Enterprise Proof-of-Access |
| `GET /api/v1/operations/health` | Plan-gated | Business or Enterprise Proof-of-Access |
| `GET /api/v1/operations/jobs` | Plan-gated | Business or Enterprise Proof-of-Access |
| `GET /api/v1/operations/liveness` | Plan-gated | Business or Enterprise Proof-of-Access |
| `GET /api/v1/operations/metrics` | Plan-gated | Business or Enterprise Proof-of-Access |
| `GET /api/v1/operations/metrics-summary` | Plan-gated | Business or Enterprise Proof-of-Access |
| `GET /api/v1/operations/providers` | Plan-gated | Business or Enterprise Proof-of-Access |
| `GET /api/v1/operations/readiness` | Plan-gated | Business or Enterprise Proof-of-Access |
| `GET /api/v1/operations/runbooks` | Plan-gated | Business or Enterprise Proof-of-Access |
| `GET /api/v1/operations/status` | Plan-gated | Business or Enterprise Proof-of-Access |
| `GET /api/v1/operator/signals/pending` | Scope-gated | Explicit scope/role + policy |
| `GET /api/v1/operator/signals/{signal_id}` | Scope-gated | Explicit scope/role + policy |
| `POST /api/v1/operator/signals/{signal_id}/approve` | Critical action | Signed request; Human Intent for mutating/export actions |
| `POST /api/v1/operator/signals/{signal_id}/confidence-override` | Scope-gated | Explicit scope/role + policy |
| `POST /api/v1/operator/signals/{signal_id}/hold` | Scope-gated | Explicit scope/role + policy |
| `POST /api/v1/operator/signals/{signal_id}/mark-false-positive` | Scope-gated | Explicit scope/role + policy |
| `POST /api/v1/operator/signals/{signal_id}/needs-more-evidence` | Scope-gated | Explicit scope/role + policy |
| `POST /api/v1/operator/signals/{signal_id}/reject` | Critical action | Signed request; Human Intent for mutating/export actions |
| `GET /api/v1/plugins` | Scope-gated | Explicit scope/role + policy |
| `GET /api/v1/plugins/{plugin_id}` | Scope-gated | Explicit scope/role + policy |
| `POST /api/v1/plugins/{plugin_id}/disable` | Critical action | Signed request; Human Intent for mutating/export actions |
| `POST /api/v1/plugins/{plugin_id}/dry-run` | Critical action | Signed request; Human Intent for mutating/export actions |
| `POST /api/v1/plugins/{plugin_id}/enable` | Critical action | Signed request; Human Intent for mutating/export actions |
| `GET /api/v1/policy/catalog` | Critical action | Signed request; Human Intent for mutating/export actions |
| `POST /api/v1/policy/catalog` | Critical action | Signed request; Human Intent for mutating/export actions |
| `POST /api/v1/policy/catalog/compare` | Critical action | Signed request; Human Intent for mutating/export actions |
| `POST /api/v1/policy/check` | Scope-gated | Explicit scope/role + policy |
| `GET /api/v1/policy/executions` | Scope-gated | Explicit scope/role + policy |
| `GET /api/v1/policy/executions/summary` | Scope-gated | Explicit scope/role + policy |
| `POST /api/v1/policy/simulate` | Scope-gated | Explicit scope/role + policy |
| `POST /api/v1/privacy/assess` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/public/features` | Public | No Proof-of-Access required |
| `GET /api/v1/public/landing` | Public | No Proof-of-Access required |
| `GET /api/v1/public/roadmap` | Public | No Proof-of-Access required |
| `GET /api/v1/public/stats` | Public | No Proof-of-Access required |
| `GET /api/v1/public/status` | Public but rate-limited | Public + strict abuse/rate limits |
| `GET /api/v1/public/trace/{report_id}/summary` | Public | No Proof-of-Access required |
| `GET /api/v1/signals/latest` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/signals/news-market-impact` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/signals/top` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/signals/{signal_id}` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/signals/{signal_id}/delivery-logs` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/signals/{signal_id}/evidence` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/signals/{signal_id}/explanation` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/signals/{signal_id}/recommendations` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/storage/status` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/storage/timescale/status` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/trace/address/{address}` | Public but rate-limited | Public + strict abuse/rate limits |
| `GET /api/v1/trace/alerts` | Access required | Default Access session for non-public API; product decision may refine |
| `POST /api/v1/trace/business/batch` | Plan-gated | Business or Enterprise Proof-of-Access |
| `GET /api/v1/trace/business/events` | Plan-gated | Business or Enterprise Proof-of-Access |
| `GET /api/v1/trace/business/policy-profiles` | Plan-gated | Business or Enterprise Proof-of-Access |
| `GET /api/v1/trace/business/profile` | Plan-gated | Business or Enterprise Proof-of-Access |
| `POST /api/v1/trace/destination-review` | Metric-entitlement-gated | Metric entitlement + policy |
| `POST /api/v1/trace/enterprise/evidence-access/evaluate` | Plan-gated | Enterprise Proof-of-Access |
| `GET /api/v1/trace/enterprise/profile` | Plan-gated | Enterprise Proof-of-Access |
| `POST /api/v1/trace/enterprise/proof-packet` | Plan-gated | Enterprise Proof-of-Access |
| `GET /api/v1/trace/enterprise/rbac/default-policy` | Plan-gated | Enterprise Proof-of-Access |
| `GET /api/v1/trace/enterprise/rbac/permissions` | Plan-gated | Enterprise Proof-of-Access |
| `GET /api/v1/trace/enterprise/rbac/roles` | Plan-gated | Enterprise Proof-of-Access |
| `GET /api/v1/trace/enterprise/sso` | Plan-gated | Enterprise Proof-of-Access |
| `GET /api/v1/trace/events` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/trace/events/{event_id}` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/trace/lite/{address}` | Public but rate-limited | Public + strict abuse/rate limits |
| `POST /api/v1/trace/payment-context` | Metric-entitlement-gated | Metric entitlement + policy |
| `POST /api/v1/trace/payment-intent/preview` | Metric-entitlement-gated | Metric entitlement + policy |
| `POST /api/v1/trace/register/payment-advisory` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/trace/report/{report_id}` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/trace/report/{report_id}/citadel-contribution` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/trace/report/{report_id}/counterparty-lens` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/trace/report/{report_id}/dust-radar` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/trace/report/{report_id}/evidence` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/trace/report/{report_id}/evidence-refs` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/trace/report/{report_id}/origin-passport` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/trace/report/{report_id}/policy-facts` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/trace/report/{report_id}/privacy-shield` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/trace/report/{report_id}/proof-packet` | Critical action | Signed request; Human Intent for mutating/export actions |
| `GET /api/v1/trace/report/{report_id}/provider-disagreement` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/trace/report/{report_id}/source-summary` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/trace/report/{report_id}/utxo-hygiene` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/trace/sources` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/trace/sources/{source_name}` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/trace/status` | Access required | Default Access session for non-public API; product decision may refine |
| `POST /api/v1/trace/treasury/destination-check` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/trace/watchlist` | Access required | Default Access session for non-public API; product decision may refine |
| `POST /api/v1/trace/watchlist` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/treasury/requests` | Scope-gated | Explicit scope/role + policy |
| `POST /api/v1/treasury/requests` | Scope-gated | Explicit scope/role + policy |
| `GET /api/v1/treasury/requests/pending-approvals` | Scope-gated | Explicit scope/role + policy |
| `POST /api/v1/treasury/requests/{request_id}/approve` | Critical action | Signed request; Human Intent for mutating/export actions |
| `POST /api/v1/treasury/requests/{request_id}/reject` | Critical action | Signed request; Human Intent for mutating/export actions |
| `GET /api/v1/users` | Plan-gated | Enterprise Proof-of-Access |
| `GET /api/v1/users/me` | Plan-gated | Enterprise Proof-of-Access |
| `POST /api/v1/wallet/health` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /api/v1/wallet/profiles` | Metric-entitlement-gated | Metric entitlement + policy |
| `POST /api/v1/wallet/profiles/{wallet_profile_id}/health` | Metric-entitlement-gated | Metric entitlement + policy |
| `GET /api/v1/wallet/profiles/{wallet_profile_id}/health/reports` | Metric-entitlement-gated | Metric entitlement + policy |
| `GET /api/v1/webhooks` | Critical action | Signed request; Human Intent for mutating/export actions |
| `POST /api/v1/webhooks` | Critical action | Signed request; Human Intent for mutating/export actions |
| `DELETE /api/v1/webhooks/{webhook_id}` | Critical action | Signed request; Human Intent for mutating/export actions |
| `GET /api/v1/webhooks/{webhook_id}` | Critical action | Signed request; Human Intent for mutating/export actions |
| `PATCH /api/v1/webhooks/{webhook_id}` | Critical action | Signed request; Human Intent for mutating/export actions |
| `GET /api/v1/webhooks/{webhook_id}/deliveries` | Critical action | Signed request; Human Intent for mutating/export actions |
| `GET /api/v1/webhooks/{webhook_id}/subscriptions` | Critical action | Signed request; Human Intent for mutating/export actions |
| `POST /api/v1/webhooks/{webhook_id}/subscriptions` | Critical action | Signed request; Human Intent for mutating/export actions |
| `DELETE /api/v1/webhooks/{webhook_id}/subscriptions/{subscription_id}` | Critical action | Signed request; Human Intent for mutating/export actions |
| `POST /api/v1/webhooks/{webhook_id}/test` | Critical action | Signed request; Human Intent for mutating/export actions |
| `GET /candles/{candle_id}` | Public | No Proof-of-Access required |
| `GET /evidence/{packet_id}` | Public | No Proof-of-Access required |
| `GET /health/dependencies` | Public | No Proof-of-Access required |
| `GET /health/intelligence` | Public | No Proof-of-Access required |
| `GET /health/live` | Public | No Proof-of-Access required |
| `GET /health/operations` | Public | No Proof-of-Access required |
| `GET /health/providers` | Public | No Proof-of-Access required |
| `GET /health/ready` | Public | No Proof-of-Access required |
| `GET /health/startup` | Public | No Proof-of-Access required |
| `GET /intelligence/timeline` | Access required | Default Access session for non-public API; product decision may refine |
| `GET /market` | Public | No Proof-of-Access required |
| `GET /market-time-machine` | Public | No Proof-of-Access required |
| `GET /market/time-machine` | Public | No Proof-of-Access required |
| `GET /market/{section}` | Public | No Proof-of-Access required |
| `GET /web/candle/{candle_id}` | Public | No Proof-of-Access required |
| `GET /web/evidence/{packet_id}` | Public | No Proof-of-Access required |
| `GET /web/market-time-machine` | Public | No Proof-of-Access required |
| `POST /web/market-time-machine/candle-click` | Public | No Proof-of-Access required |
| `POST /web/market-time-machine/evidence-view` | Public | No Proof-of-Access required |
| `POST /web/market-time-machine/marker-click` | Public | No Proof-of-Access required |
| `POST /web/market-time-machine/replay-open` | Public | No Proof-of-Access required |
| `GET /web/timeline` | Public | No Proof-of-Access required |

## Ambiguous endpoints needing product decision

- Market/news/intelligence read APIs are currently classified as Access required by default unless explicitly public; product should decide which remain free public previews versus plan-gated premium intelligence.
- Health readiness/liveness and public status endpoints remain public; provider/runtime/operations health endpoints are protected because they can reveal infrastructure details.
- Legacy `/api/v1/auth/*` endpoints remain public only to return `legacy_auth_disabled`.

## Validation Notes

- `pytest -q` currently fails in repository-wide execution because async MCP/SDK tests use `pytest.mark.asyncio` without an active async test plugin in this environment. Access endpoint/security targeted suites are expected to pass.
- `pytest tests/integration/ -q` currently includes older integration assertions that expect newly protected admin, metrics, trace, business, enterprise, treasury, and webhook-management endpoints to remain public or legacy-admin accessible; those failures are expected follow-up test migrations for Prompt 22 and are covered by the new protected-endpoint integration suite.
- `ruff check .` currently reports pre-existing script lint issues under `scripts/` (`E402`, `F401`, `E701`, `E702`) unrelated to Access endpoint protection.
