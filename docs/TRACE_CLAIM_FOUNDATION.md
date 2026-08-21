# Trace Multi-Source Claim Foundation

## Scope and ownership

D1 introduces immutable analytical Claims and comparable-claim collection. It does
not evaluate disagreement, select a winner, create Graph relationships, or expose a
public Claim API.

| Concept | Owner |
| --- | --- |
| Blockchain fact | T1 Observation |
| Bitcoin relation | T2 Relationship |
| Topology computation | T3 Topology Engine |
| Graph projection | T4 / Graph Domain |
| Analytical assertion | Claim Producer |
| Comparable-claim collection | D1 `TraceClaimCollector` |
| Disagreement evaluation | D2 (not implemented) |
| Privacy browser exposure | Trace Privacy Policy |
| UI rendering | Prompt 13 |

## Producer inventory

| Producer | Input | Subject | Predicate | Source | Classification |
| --- | --- | --- | --- | --- | --- |
| Baseline risk-band producer | existing `TraceScoringResult` | Bitcoin address | `RISK_BAND` | `baseline_internal_rules` | authoritative method claim; unchanged baseline semantics |
| Address-syntax network producer | validated public Bitcoin address encoding | Bitcoin address | `BITCOIN_NETWORK` | `bitcoin_address_encoding` | deterministic local method claim |
| Observation-source network producer | T1 `AddressObserved` provenance | Bitcoin address | `BITCOIN_NETWORK` | actual observation provider | authoritative source-backed claim |
| Risk source registry | configuration/status rows | none | none | configured registry | source configuration only |
| Provider health/failure | operational state | none | none | provider | operational only; never a Claim |
| Hard-coded origin `unknown` | placeholder | none | none | none | removed from disagreement inputs; never a Claim |

The first comparable domain is `(Bitcoin address, BITCOIN_NETWORK)`. Address encoding
and source metadata are independent in the product sense: one is a deterministic
local parsing method over the public identifier; the other is metadata asserted by
the authoritative T1 observation source. They do not call the same computation or
copy one result. Both are useful even when they agree.

## Claim model

Claims have a typed Bitcoin-address subject, typed predicate, discriminated value,
stable producer and source identities, capture identity, method version, evaluation
time, immutable input references, limitations, and nullable confidence. Confidence
is present only for the existing scorer, which owns it; deterministic network claims
do not fabricate confidence.

Claim identity hashes schema version, capture, subject, predicate, producer, method
version, source, typed value, and immutable input references. Independent producers
therefore remain separately attributable even when they emit equal values. A
same-producer semantic duplicate has the same ID and is deduplicated by the collector
and append-only repository.

## Production lifecycle

After a Trace report receives its persistent ID, `TraceService` obtains the report's
currently persisted on-chain source events, emits T1 observations, invokes the claim
collector, and stores results in `trace_claims`. The collector orders producers and
claims deterministically and preserves typed non-success outcomes:

* `SUCCESS_WITH_CLAIM`;
* `NO_APPLICABLE_CLAIM`;
* `INSUFFICIENT_DATA`;
* `SOURCE_UNAVAILABLE`;
* `PRODUCER_FAILURE`.

These statuses are not disagreement. In particular, no observation means source
unavailable rather than an `UNKNOWN` network claim.

## Persistence and history

Claims are append-only analytical results keyed by deterministic Claim ID and linked
to a report capture. Their scalar typed value and identity fields are relational;
bounded immutable input references and limitations use deterministic JSON arrays.
Historical report A reads its own captured Claim rows and cannot acquire claims from
later report B. Migration `20260815_0074` adds the table without changing existing
report rows. During rolling deployment, old schemas without the table preserve report
behavior and simply report Claim persistence unavailable until migration completes.

## Boundaries and limitations

The network claims establish real comparable sources but do not imply that a conflict
exists. D2 may compare only claims with the same subject and predicate and must keep
source failure/missingness separate. No ownership, counterparty, clustering, AML,
Graph edge, or browser semantics are introduced. No external SaaS is required.

## Rollback

Rollback may stop Claim collection, remove the D1 producers/collector, and downgrade
the `trace_claims` table only under an explicit data-retention decision. T1-T4, G1-G4,
Graph snapshots, reports, topology, privacy policy, and user data remain intact.
Without D1, disagreement readiness returns to unavailable; no fallback claim may be
fabricated.
