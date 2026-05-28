# Market Time Machine Ingestion

Pipeline: Source -> Fetch -> Parse -> Normalize -> Canonicalize -> Clean -> Hash -> Duplicate precheck -> Persist -> Metrics/logs.

Evidence-first replay: stores raw payload metadata, fetch metadata, and deterministic hashes.
