# Workers

Owns background job processors, Celery workers, long-running consumers and asynchronous execution safety.

Current canonical paths:

- `app/tasks/`
- worker-oriented services under `app/services/`
- deployment manifests for worker processes

Migration rule: workers must be idempotent where possible and expose operational evidence for failures, retries and completion.
