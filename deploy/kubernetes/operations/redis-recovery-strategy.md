# Redis recovery strategy
- Cache-only mode: acceptable cache loss, warm-up after restart.
- Celery broker mode: queue loss risk if Redis is lost without persistence.
- Require idempotent jobs and safe retry semantics.
- Use managed Redis or persistence when queue durability is required.
- After Redis loss: restart Redis, then workers in controlled order; monitor duplicate suppression and delivery behavior.
