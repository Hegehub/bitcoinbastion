# Scheduler

Owns periodic jobs, Celery beat schedules, cron-style runtime tasks, provider health checks and recovery drills.

Current canonical paths:

- `app/tasks/`
- scheduler settings in configuration
- scheduled Kubernetes/CronJob manifests under `deploy/`

Migration rule: every scheduled task must document cadence, owner, timeout, idempotency and failure escalation.
