# Observability stack

Owns the integrated metrics, logs, traces, dashboards, runtime evidence snapshots and operational visibility model.

Current canonical paths:

- `app/services/observability/`
- `app/core/telemetry.py`
- observability/deployment documentation under `docs/` and `deploy/`

Migration rule: observability must provide explainable evidence, not only raw telemetry.
