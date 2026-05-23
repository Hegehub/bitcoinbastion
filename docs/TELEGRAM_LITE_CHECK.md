# Telegram Lite /check Baseline

Current repository has Telegram bot infrastructure, but `/check` command integration is pending.

Planned baseline behavior:
- `/check <bitcoin_address>` validates public address only.
- Rejects seed/private-key-looking input.
- Returns Lite plain-language advisory summary.
- Never signs or broadcasts transactions.
