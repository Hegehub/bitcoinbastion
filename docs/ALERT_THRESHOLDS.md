# Alert Thresholds

Operational alert thresholds for Bitcoin Bastion runtime.

## Jobs (24h window)
- `warning`: failed jobs >= 3
- `critical`: failed jobs >= 10

## Deliveries (24h window)
- `warning`: failed deliveries >= 2
- `critical`: failed deliveries >= 6

## Policy/Treasury governance
- `warning`: repeated high-risk policy simulation outcomes without activation notes.
- `critical`: high-risk policy tightening attempts without `change_justification`.

## Actions
- Warning: investigate in business hours, track trend in recovery check.
- Critical: immediate operator escalation and rollout freeze until root cause identified.
