# Deployment Evidence Pack

Use `python scripts/collect_release_evidence.py` to generate JSON release evidence into `artifacts/`.

## Captured fields
- commit SHA
- timestamp
- environment
- lint/test/contract/regression results
- migration smoke result
- postgres schema parity result
- health/readiness result
- observability snapshot result
- recovery-check result
- metrics scrape result
- known limitations acknowledgement

## Notes
Some checks (observability snapshot, recovery-check, metrics scrape) require deployed runtime/API access; placeholders are recorded when unavailable.
