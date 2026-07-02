# Data warehouse

Owns analytical datasets, historical aggregates, reporting storage, retention strategy and long-horizon market intelligence data products.

Current canonical paths:

- analytics/intelligence services under `app/services/`
- generated evidence/artifact outputs under `artifacts/`

Migration rule: warehouse data must have lineage, freshness metadata and a clear source-of-truth relationship to operational storage.
