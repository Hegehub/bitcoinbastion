# Bitcoin Topology Engine

## Topology architecture

`BitcoinTopologyEngine` is a backend-only analytical service that constructs deterministic topology exclusively from authoritative `BitcoinTopologyRelationship` inputs. It does not consume reports, UI state, graph projections, risk scores, AML classifications, ownership labels, or browser layout.

## Topology model

A topology owns immutable nodes, relationships, directed adjacency, reverse adjacency, limitations, topology version, engine version, and deterministic topology identity. Nodes retain originating relationship IDs, originating observation IDs, and limitations.

## Traversal architecture

Supported operations are deterministic adjacency lookup, directed descendants, directed ancestors, reachability, shortest directed path, weak connected component discovery, and temporal relationship filtering. Traversal order is sorted and deterministic.

## Snapshot model

`BitcoinTopologySnapshot` is immutable analytical state for one topology build. It is distinct from Trace Graph snapshots and report snapshots. It contains topology id, topology version, engine version, network, authoritative capture time, immutable node/relationship mappings, sorted identities, and limitations.

## Validation architecture

The engine validates duplicate relationship identities, empty relationship IDs, missing source/target objects, and broken provenance. It rejects invalid relationship inputs instead of returning partial topology.

## Provenance architecture

Topology nodes aggregate originating relationship IDs and originating observation IDs from relationship provenance. Relationship provenance remains the authority for producer, builder version, blockchain source metadata, and limitations.

## Persistence decisions

No topology table is introduced. Topology is a deterministic immutable materialization from persisted append-only `OnchainEvent` source facts. Historical captures use content-addressed source-event prefixes, avoiding duplicate authoritative storage while retaining exact topology-to-Graph snapshot linkage.

## Performance decisions

The engine builds adjacency maps in a single pass over relationships and uses deterministic BFS for traversal. Incremental rebuild is represented by rebuilding from an existing immutable relationship set; no speculative cache is introduced.

## Boundaries

The engine does not implement UI, visualization, replay, history UI, similarity UI, clustering, entity resolution, counterparty inference, ownership inference, AML analytics, or money-flow scoring.

## T4 integration

`BitcoinTopologyGraphAdapter` now connects snapshots into Trace Graph without recomputing topology. More expressive topology still requires authoritative input/output/spend/UTXO/block/script relationship producers before those relationship types can appear.

## Rollback

Rollback can remove `app/services/bitcoin_topology/engine.py`, the engine export, this document, and engine tests. Observation layer, relationship layer, Graph Domain, Graph Builder, history, reports, persistence, and user data remain intact.
