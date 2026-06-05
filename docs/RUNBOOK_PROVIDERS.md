# Runbook: Providers

## Signals
- Provider confidence collapses.
- RSS/BTC/news provider health is degraded.
- Backoff is active or source diversity is low.

## Actions
1. Identify affected provider and degraded_reason.
2. Activate fallback provider if configured.
3. Keep degraded provider visible in confidence and evidence limitations.
4. Store drill evidence with type `provider_outage` or `rss_outage`.
