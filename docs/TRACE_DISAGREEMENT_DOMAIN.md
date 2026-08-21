# Trace Disagreement Domain

## Actual comparable domain

D2 begins with the reviewed D1 pair rather than a universal comparator:

| Subject | Predicate | Value | Producer A | Producer B | Comparable |
| --- | --- | --- | --- | --- | --- |
| Bitcoin address | `BITCOIN_NETWORK` | `BitcoinNetworkClaimValue` | `bitcoin-address-syntax-network` v1 | `bitcoin-observation-source-network` v1 | Yes: both classify the mutually exclusive Bitcoin network of the same address at one capture |
| Bitcoin address | `RISK_BAND` | `RiskBandClaimValue` | baseline scorer | none | No: fewer than two reviewed independent producers |
| Bitcoin address | mixed predicates | heterogeneous | any | any | No: different analytical questions |
| different address subjects | same predicate | same value type | any | any | No: different analytical subjects |

Independence is enforced using the D1-reviewed producer pair. Multiple observations
from the observation producer do not independently satisfy the minimum producer
count. Failure, source unavailability, insufficient data, and unsupported producer
results are coverage states, never alternatives.

## Claim Set

`TraceClaimSet` contains all eligible independent Claims for one subject, predicate,
and immutable report capture. Its stable ID hashes capture, subject, predicate, and
sorted Claim IDs. Input order therefore has no semantic effect. Different subjects,
predicates, or capture boundaries are rejected as `NOT_COMPARABLE`.

## Comparator semantics

The only v1 comparator is `BitcoinNetworkClaimComparator`. It accepts the strict
`BitcoinNetworkClaimValue` union member and the reviewed syntax/observation producer
pair. `bitcoin-mainnet` and `bitcoin-testnet` are mutually exclusive classifications:

* all eligible reviewed producers return the same canonical network → `AGREEMENT`;
* eligible reviewed producers return more than one canonical network → `DISAGREEMENT`;
* unsupported network, wrong value type, wrong predicate, or missing reviewed
  producer → `NOT_COMPARABLE` or `INSUFFICIENT_COMPARABLE_CLAIMS`.

There is no generic raw-value comparator, numeric tolerance, severity, conflict
score, confidence averaging, majority vote, recency winner, or highest-confidence
winner.

## Evaluator result and resolution

The result taxonomy is `AGREEMENT`, `DISAGREEMENT`,
`INSUFFICIENT_COMPARABLE_CLAIMS`, and `NOT_COMPARABLE`. Both agreement and
disagreement retain each typed participating Claim and source attribution.
Per-Claim confidence is unchanged.

The resolution audit is **R1 — NO_RESOLUTION_AUTHORITY**. A disagreement is explicitly
`UNRESOLVED`; `canonical_claim_id` is always absent in evaluator v1. Agreement and
non-comparison use `NOT_APPLICABLE`. No Graph topology is created or mutated.

## Historical and persistence policy

D2 uses **D2P2**: derive deterministically from D1's immutable, report-captured Claim
rows. Persisting a second disagreement record would duplicate authority. Historical
report A loads only Claim A identities, values, producer versions, and capture ID,
then evaluates with `trace-disagreement-evaluator-v1`. Later report B Claims cannot
enter A, so historical disagreement future-data leakage is zero.

Claim producer version and evaluator version are separate. A future comparator must
receive a new evaluator version; historical values are never rerun through a changed
producer. Exact Graph Snapshot integration in D3 may reference this immutable report
Claim set but must not use current Claims for historical reads.

## Privacy and safe sources

D2 models are internal. They retain logical source IDs, not provider credentials,
URLs, request payloads, headers, or debug data. D3 browser projection must pass Claims
and evaluations through the centralized Trace Privacy Policy and construct an
explicit safe source reference. D2 exposes no API or frontend contract.

## Performance and observability

Claims are grouped by typed subject and predicate before evaluation. Evaluation is
linear in the bounded Claim count for one analytical question. Metrics count outcomes
and duration using status-only labels; addresses and transaction IDs are never metric
labels.

## Boundaries and rollback

Claim Producers emit assertions; D1 collects them; D2 compares reviewed eligible
Claim Sets; Graph supplies stable analytical identity; privacy controls future
exposure; Prompt 13 presents results. D2 performs no UI work and no Evidence
verification.

Rollback can remove the comparator, Claim Set, evaluator, historical derivation,
metrics, tests, and this document while preserving D1 Claims, T1-T4, G1-G4, Graph
Snapshots, reports, privacy policy, and user data. Disagreement then becomes
unavailable; comparison must not move to the frontend.
