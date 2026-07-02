# Queue

Owns asynchronous broker topology, queue naming, retry semantics, dead-letter strategy and producer/consumer contracts.

Current canonical paths:

- `app/tasks/`
- Celery and Redis settings in runtime configuration

Migration rule: every queue must document ownership, retry policy, idempotency expectations and failure behavior.
