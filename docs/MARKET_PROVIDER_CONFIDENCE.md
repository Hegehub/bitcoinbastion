# Market Provider Confidence

Provider confidence for candles is computed from provider count, disagreement, degraded status, and health-aware penalties.

## Time-Series Confidence Events

Prompt 15 adds TimescaleDB-compatible provider/source confidence event tables for historical confidence changes. PostgreSQL remains canonical for provider definitions and policy decisions; TimescaleDB stores historical observations that support dashboards, degraded-mode evidence, and later analytics projections.

Confidence events should capture bounded fields such as provider/source key, domain, event type, previous/new confidence, confidence delta, reason code, status, degraded state, and safe metadata. They must not contain raw provider credentials, API tokens, seed phrases, Bitcoin private keys, wallet files, xprv/yprv/zprv, bearer secrets, or unredacted provider URLs.

ClickHouse remains future Market Time Machine analytics work. Provider confidence history may later be projected to ClickHouse through the storage outbox, but route handlers and collectors must not perform ad-hoc cross-database writes.
