# Monitoring

Owns metrics, health probes, readiness checks, SLO signals, Prometheus/ServiceMonitor integration and runtime health evidence.

Current canonical paths:

- `app/core/telemetry.py`
- health endpoints under `app/api/`
- deployment monitoring manifests under `deploy/`

Migration rule: monitoring must distinguish healthy, degraded, synthetic, fallback and failed runtime states explicitly.
