# Tests

Owns test strategy, fixtures, unit/integration/smoke checks, release evidence checks and regression coverage.

Current canonical paths:

- `tests/`
- test-related Makefile and CI targets

Migration rule: architecture moves must be covered by tests that prove imports, routers, migrations and runtime entrypoints still work.
