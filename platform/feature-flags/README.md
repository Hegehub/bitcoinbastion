# Feature flags

Owns runtime feature gates, staged rollout controls, kill switches, environment-specific toggles and feature lifecycle documentation.

Current canonical paths:

- `app/core/config.py`
- feature-gated services/routes as they are introduced

Migration rule: feature flags must have owners, default values, rollback behavior and removal criteria.
