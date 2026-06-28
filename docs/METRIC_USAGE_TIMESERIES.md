# Metric Usage Time-Series

## Purpose

Metric usage events record operational usage over time for API requests, metric queries, SDK/CLI/MCP calls, webhooks, WebSocket messages, access-integrity changes, signal score observations, quota decisions, and future business/enterprise reports.

TimescaleDB is used because these records are append-only, time-windowed, and naturally queried by ranges, metric groups, and privacy-safe subject hashes. The table also works as a normal PostgreSQL-compatible table when TimescaleDB is disabled or unavailable.

## What Metric Usage Events Are Not

Metric usage events are not canonical truth for Access Certificates, Subscription Entitlements, Payment Proofs, Revocation Records, Recovery Quorums, or Policy Rules. Those remain PostgreSQL transactional truth. Future billing or quota decisions may reconcile PostgreSQL truth with time-series usage, but this foundation does not implement billing, payment flows, Access Pass issuance, or final quota enforcement.

## Data Model

`metric_usage_events` stores:

- event type and decision;
- metric group, metric name, feature code, endpoint template, method, and status code;
- credit cost and request count;
- privacy-safe hashes for pass/workspace/API-key/session subjects;
- optional SDK/client/source-component labels;
- risk, policy, denial, and safe metadata fields;
- `recorded_at` as the Timescale hypertable time column.

## Privacy-Safe Identifiers

Subject fields such as `pass_lookup_hash`, `workspace_id_hash`, `api_key_hash`, and `session_id_hash` must contain hashes or fingerprints only. Do not store emails, phone numbers, names, raw IP addresses, raw Bitcoin addresses, raw API keys, raw session tokens, raw Access Pass bearer values, or raw Telegram user IDs.

## Forbidden Data

Metric usage metadata must not contain seed phrases, mnemonics, Bitcoin private keys, wallet files, xprv/yprv/zprv, passwords, raw tokens, API keys, access tokens, session tokens, auth headers, object-storage credentials, or unredacted secrets.

## Degraded Mode

If TimescaleDB is unavailable, writes should still work against the normal PostgreSQL-compatible table where the application database is reachable. Storage health should report metric usage time-series as degraded when TimescaleDB is enabled but the hypertable is unavailable. Analytics, dashboards, and reports may be limited; critical access truth remains in PostgreSQL.

## Future Work

Prompt 16 does not implement the full Metric Catalog, Subscription Entitlement Overlay, billing, payment flows, or quota enforcement. Future prompts should add instrumentation at approved service boundaries, PostgreSQL rollups where needed for access decisions, outbox-driven ClickHouse projections for long-range analytics, and retention/compression policies.
