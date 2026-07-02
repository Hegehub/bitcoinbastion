# Search

Owns search indexes, discovery surfaces, query normalization and future search provider integration.

Current canonical paths:

- search-like service code under `app/services/`
- API search/query endpoints as they are introduced

Migration rule: search indexes must be rebuildable from canonical persisted data and must expose freshness/staleness metadata.
