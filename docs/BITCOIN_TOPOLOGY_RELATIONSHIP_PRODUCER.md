# Bitcoin Topology Relationship Producer

## Relationship architecture

Bitcoin topology relationships are immutable backend analytical facts reproducible from canonical Bitcoin observations. They are not UI edges, graph layout, clustering, risk assessment, ownership inference, or counterparty inference.

## Relationship type hierarchy

The only relationship type currently supported is `ADDRESS_PARTICIPATES_IN_TRANSACTION`. It is emitted only when an `AddressObserved` and a `TransactionObserved` share the same normalized transaction id. Input/output/spend/UTXO/block relationships are intentionally deferred because the current observation layer does not yet emit those fact types.

## Producer architecture

`BitcoinTopologyRelationshipProducer` is the canonical backend component permitted to construct Bitcoin topology relationships from observations. It consumes immutable observations, validates provenance and duplicate identities, constructs deterministic relationships, assigns stable identities, preserves provenance, and never constructs Trace Graph objects or APIs.

## Identity strategy

Relationship identities use `bitcoin-topology-relationship-v1`, relationship type, source object id, target object id, and originating observation ids. Source and target object ids are also deterministic over relationship version, object type, and canonical value.

## Direction semantics

`ADDRESS_PARTICIPATES_IN_TRANSACTION` is directed from address object to transaction object. Direction is based on the factual event record and never on visualization convenience.

## Provenance strategy

Every relationship records producer, builder version, originating observation ids, blockchain source metadata, and limitations. Limitations include `no_ownership_inference` and `no_counterparty_inference`.

## Validation strategy

The producer rejects duplicate observation identities, missing provenance producers, missing provenance sources, and unsupported relationship types. Duplicate relationship outputs are merged by stable relationship id.

## Persistence decisions

No new relationship table is introduced in T2. Relationships are deterministic immutable projections from persisted `OnchainEvent` observations. This avoids duplicate storage while preserving compatibility. Durable relationship persistence can be introduced later only if it remains derived from observations and does not become an independent source of truth.

## Boundaries

The producer does not emit `SAME_OWNER`, `SAME_ENTITY`, `LIKELY_OWNER`, `COUNTERPARTY`, `CLUSTER_MEMBER`, `EXCHANGE`, `MIXER`, `SERVICE`, `PERSON`, or `ORGANIZATION` relationships.

## Remaining blockers before T3

T3 can integrate this relationship producer into graph construction for `ADDRESS_PARTICIPATES_IN_TRANSACTION`. More detailed topology relationships remain blocked on producers for input, output, spend, UTXO, block, and script observations.

## Rollback

Rollback can remove `app/services/bitcoin_topology/`, this document, and topology relationship tests. The Observation layer, Graph Domain, Graph Builder, snapshots, history, reports, persistence, and user data remain intact.
