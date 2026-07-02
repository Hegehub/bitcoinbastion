# Distributed tracing

Owns trace context propagation, span naming, request correlation across services and future OpenTelemetry integration.

Current canonical paths:

- `app/core/telemetry.py`
- middleware/request correlation code under `app/api/`

Migration rule: tracing must be low-cardinality, privacy-aware and correlated with logs/metrics without exposing secret values.
