# MARKET DATA ENGINE

Bitcoin Bastion uses a Bitcoin-first public market provider layer for BTC/USD context (not trading execution).

## Provider architecture
- Providers: Binance, Kraken, Coinbase, Bitstamp (public no-key endpoints).
- Isolated provider adapters with validation and failure isolation.

## Aggregation logic
- Deterministic median aggregation.
- Outlier pruning by spread threshold.
- Degraded state surfaced when only one provider is available or spread is too large.

## Confidence logic
- Confidence is degraded by failures, consecutive failures, latency, and provider disagreement.
- Confidence always explicit in API responses.

## Replay philosophy
Persisted price points include provider, timestamps, latency, confidence, aggregation round, and metadata.

## Limitations
Public endpoints may fail or rate-limit; this is an evidence/context subsystem only.
No trading execution, no custody, no financial advice.
