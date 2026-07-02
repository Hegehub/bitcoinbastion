# Logging

Owns structured logging, request correlation, request IDs, log redaction, log shipping contracts and operational log quality.

Current canonical paths:

- `app/core/logging.py`
- `app/api/middleware.py`
- logging-related tests and docs

Migration rule: logs must be useful for incident response without leaking secrets, credentials or sensitive operator data.
