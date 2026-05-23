# Bastion Trace Observability

## Metrics
Bastion Trace metrics are baseline and must use bounded labels only.

Allowed labels: `tier`, `band`, `status`, `event_type`, `source_type`, `severity`, `operation`.

Forbidden labels:
- Bitcoin addresses
- `report_id`
- `user_id`
- any unbounded raw error or provider identifiers

## Runtime events and alerts
- Runtime events are implemented as operational records for trace lifecycle and health signals.
- Alert objects are placeholders unless delivery infrastructure is configured.

## Status endpoint
- Trace status is operational visibility and not a production-calibration claim.
- `trace_production_calibrated` remains `false` until real evidence exists.

## Telegram
- Telegram commands are advisory and never request seed phrases/private keys.
- Production command delivery depends on configured bot/runtime infrastructure.
