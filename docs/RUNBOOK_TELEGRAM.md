# Runbook: Telegram Outage

## Signals
- Telegram health is degraded or critical.
- Publication failures increase.

## Actions
1. Keep API and web online.
2. Stop automatic publication if failures repeat.
3. Queue or hold signals for operator review.
4. Notify operators through alternate channel and store drill evidence with type `telegram_outage`.
