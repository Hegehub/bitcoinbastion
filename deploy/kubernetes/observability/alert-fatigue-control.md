# Alert fatigue control
- Severity levels: critical/warning/info.
- Paging only for sustained critical alerts.
- Grouping by alertname+namespace.
- Inhibit warning when matching critical active.
- Maintenance window muting required for planned ops.
- Noisy providers should route to ops warning channel first.
- Manual acknowledgement required for prolonged degraded/evidence stale alerts.
