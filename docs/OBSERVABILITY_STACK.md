# Observability Stack

Observability stack is baseline and requires tuning.
Prometheus/Grafana/Loki/Alerting are placeholders requiring production retention and alert thresholds.

Wallet-first and LNURL security telemetry now uses the existing `/metrics` endpoint
and ServiceMonitor. Controlled labels, metric groups, dashboards, alerting guidance,
and privacy constraints are documented in
[`WALLET_LNURL_OBSERVABILITY.md`](WALLET_LNURL_OBSERVABILITY.md). Metrics are
operational aggregates and are never authorization or audit evidence.

## Provider and Source Health History

Provider/source health history is now represented as a Storage Layer time-series concern. The operational path is:

```text
provider/source check result
→ PostgreSQL transaction with health time-series row
→ optional storage outbox event
→ future dashboard / ClickHouse / evidence projections
```

TimescaleDB is the intended operational time-series store for historical provider health, source health, confidence events, source registry health metrics, runtime degradation observations, and market/news source reliability history. PostgreSQL remains transactional truth for canonical provider/source definitions and policy decisions. Redis may cache current status but must not be durable truth.

If TimescaleDB is disabled or unavailable, critical transactional APIs should not fail solely because historical provider/source health storage is degraded. Operator dashboards, trust matrices, and release evidence should show degraded mode and rely on the outbox/retry path where configured.

Observability payloads must avoid secrets: no seed phrases, Bitcoin private keys, wallet files, xprv/yprv/zprv, API secrets, auth headers, private provider credentials, or sensitive URLs.
