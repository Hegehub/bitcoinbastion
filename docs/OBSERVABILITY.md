# Production Observability

Bitcoin Bastion follows a **no invisible failures** operating model: degraded providers, failed jobs, blocked evidence generation, rejected signals and Telegram publication failures are surfaced through API DTOs and Prometheus-compatible metrics.

## Monitoring model

Collectors, storage, analysis, evidence, signals and interfaces emit bounded operational signals that roll into:

- `system_health_snapshots`
- `provider_health_snapshots`
- `background_job_health`
- `service_health_snapshots`
- `runtime_state_snapshots`
- `degraded_component_snapshots`
- `recovery_events`

Global health states are `healthy`, `degraded`, `critical`, `maintenance` and `offline`.

## Provider visibility

Provider health tracks provider name/type, success/failure timestamps, failure counts, consecutive failures, latency, confidence, backoff and health state. Supported provider families include RSS, Bitcoin price providers, regulatory feeds, official blogs, Telegram and internal schedulers.

Provider degradation is never hidden. It lowers provider confidence and must be reflected in downstream signal confidence and evidence limitations.

## Prometheus metrics

The runtime registers bounded-label metrics for RSS fetches, BTC price collection, news events, impacts, candle attributions, signals, evidence packets, replay, Telegram publications, provider degradation, background jobs and operator reviews.

Allowed labels are only `provider`, `signal_type`, `job_name`, `status` and `reason_code`. URLs, article titles, hashes, database IDs and free text are not permitted.

## Grafana and alerts

Dashboard definitions now cover Platform Overview, Intelligence, Providers, Evidence, and Operator activity. Alert rules cover critical database, worker, provider confidence, Telegram, migration, and evidence-integrity failures plus warning-level RSS, latency, source-diversity, replay, and queue/job-growth conditions.

The preferred root probe endpoints are `/health/live`, `/health/ready`, `/health/startup`, `/health/dependencies`, `/health/providers`, `/health/intelligence`, and `/health/operations`.

## Task 47 metrics and DR alerting

Operational metrics include article processing, market price points, BTC candles, price impacts, candle attributions, similarity queries, signals, evidence, provider failures, timeline failures, CronJob failures, DR recovery runs and backup validation runs. Alert rules now include all providers offline, timeline failure, replay failure, integrity mismatch, scheduler stalled, database degraded, signal queue overflow, backup validation failure and restore validation failure.
