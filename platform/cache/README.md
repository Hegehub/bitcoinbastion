# Cache

Owns Redis-backed cache policy, TTL design, invalidation rules and cache-related runtime configuration.

Current canonical paths:

- `app/core/config.py`
- Redis integration points in services/tasks

Migration rule: cache entries must be explicitly scoped, bounded by TTL and safe to rebuild from source-of-truth data.
