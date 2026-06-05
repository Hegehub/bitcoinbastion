# Runbook: Workers

## Signals
- Background job status is degraded or critical in `/health/operations`.
- `BitcoinBastionWorkerStopped` or background job alerts fire.

## Actions
1. Check worker deployment and queue depth.
2. Restart workers only after recording failed jobs.
3. Replay failed jobs or explicitly mark them operator-confirmed.
4. Store drill evidence with type `worker_restart`.

## Safety
Never hide failed jobs or mark queues healthy until last_success and last_failure are visible.
