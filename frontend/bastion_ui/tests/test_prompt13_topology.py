from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from bastion_ui.domain.prompt13 import (
    adapt_trace_disagreements,
    adapt_trace_graph,
    adapt_trace_history,
)
from bastion_ui.domain.prompt13_scenarios import PROMPT13_SCENARIOS
from bastion_ui.domain.provenance import ProvenanceState
from bastion_ui.topology import ROUTE_BY_ID
from bastion_ui.transport.generated_schemas import (
    SafeTraceDisagreementCollectionDTO,
    TraceGraphDTO,
    TraceGraphHistoryDTO,
)


def _graph() -> TraceGraphDTO:
    provenance = {
        "producer": "bitcoin-topology-graph-adapter-v1",
        "stage": "T4",
        "observations": ["observation:1"],
        "evidence": [],
        "limitations": [],
        "source_relationship_id": "relationship:1",
        "topology_snapshot_id": "topology:1",
    }
    metadata = {
        "graph_id": "graph:1",
        "graph_version": "trace-graph-v1",
        "snapshot_version": "trace-snapshot-v1",
        "api_version": "trace-graph-api-v1",
        "schema_version": "trace-graph-schema-v1",
        "builder_version": "trace-graph-builder-v1",
        "analysis_version": "baseline-trace-v1",
        "chain": "bitcoin",
        "graph_hash": "digest",
        "created_at": datetime(2026, 8, 15, tzinfo=UTC),
        "limitations": [],
        "topology_source_status": "authoritative",
        "topology_snapshot_id": "topology:1",
        "topology_version": "bitcoin-topology-v1",
        "topology_engine_version": "bitcoin-topology-engine-v1",
        "topology_network": "bitcoin-mainnet",
    }
    return TraceGraphDTO.model_validate(
        {
            "metadata": metadata,
            "objects": [
                {
                    "id": "address:1",
                    "kind": "bitcoin_address",
                    "label": "bc1q…",
                    "provenance": provenance,
                    "limitations": [],
                },
                {
                    "id": "transaction:1",
                    "kind": "bitcoin_transaction",
                    "label": "tx1",
                    "provenance": provenance,
                    "limitations": [],
                },
            ],
            "relationships": [
                {
                    "id": "relationship:1",
                    "source_id": "address:1",
                    "target_id": "transaction:1",
                    "relationship_type": "address_participates_in_transaction",
                    "direction": "directed",
                    "originating_observation_id": "observation:1",
                    "provenance": provenance,
                    "confidence": Decimal("0.8"),
                    "limitations": [],
                }
            ],
            "observations": [],
            "snapshot": {
                "snapshot_id": "trace_snapshot:a",
                "graph_id": "graph:1",
                "metadata": metadata,
                "object_ids": ["address:1", "transaction:1"],
                "relationship_ids": ["relationship:1"],
                "observation_ids": [],
                "report_fact_ids": [],
                "topology_snapshot_id": "topology:1",
            },
        }
    )


def test_feature54_projects_authoritative_nodes_edges_and_history_without_inference() -> None:
    graph = _graph()
    topology = adapt_trace_graph(graph)
    assert [node.id for node in topology.nodes] == ["address:1", "transaction:1"]
    assert topology.relationships[0].relationship_type == "address_participates_in_transaction"
    assert topology.relationships[0].direction == "directed"

    history = TraceGraphHistoryDTO.model_validate(
        {
            "graph_id": "graph:1",
            "entries": [
                {
                    "snapshot_id": "trace_snapshot:a",
                    "graph_id": "graph:1",
                    "graph_version": "trace-graph-v1",
                    "snapshot_version": "trace-snapshot-v1",
                    "api_version": "trace-graph-api-v1",
                    "schema_version": "trace-graph-schema-v1",
                    "builder_version": "trace-graph-builder-v1",
                    "analysis_version": "baseline-trace-v1",
                    "created_at": datetime(2026, 8, 15, tzinfo=UTC),
                    "provenance_summary": [],
                    "limitations": [],
                    "topology_source_status": "authoritative",
                    "topology_snapshot_id": "topology:1",
                }
            ],
        }
    )
    assert adapt_trace_history(history)[0].snapshot_id == "trace_snapshot:a"


def test_feature54_preserves_backend_disagreement_status_and_attribution() -> None:
    payload = SafeTraceDisagreementCollectionDTO.model_validate(
        {
            "graph_snapshot_id": "trace_snapshot:a",
            "evaluations": [
                {
                    "evaluation_id": "evaluation:1",
                    "status": "agreement",
                    "resolution_status": "not_applicable",
                    "subject": {
                        "kind": "bitcoin_address",
                        "object_id": "address:1",
                        "public_value": "bc1q…",
                    },
                    "predicate": "bitcoin_network",
                    "claims": [
                        {
                            "id": "claim:1",
                            "subject": {
                                "kind": "bitcoin_address",
                                "object_id": "address:1",
                                "public_value": "bc1q…",
                            },
                            "predicate": "bitcoin_network",
                            "value": {"kind": "bitcoin_network", "network": "bitcoin-mainnet"},
                            "producer": "address-syntax",
                            "source": "address",
                            "producer_version": "v1",
                            "evaluated_at": datetime(2026, 8, 15, tzinfo=UTC),
                            "confidence": None,
                            "provenance": {"input_references": ["address:1"], "limitations": []},
                            "limitations": [],
                        }
                    ],
                    "coverage": {
                        "eligible_claim_count": 2,
                        "eligible_producer_count": 2,
                        "failed_producer_count": 0,
                        "insufficient_producer_count": 0,
                        "unavailable_producer_count": 0,
                    },
                    "evaluator_version": "trace-disagreement-evaluator-v1",
                    "graph_snapshot_id": "trace_snapshot:a",
                    "limitations": [],
                }
            ],
        }
    )
    view = adapt_trace_disagreements(payload)
    assert view.evaluations[0].status == "agreement"
    assert view.evaluations[0].claims[0].producer == "address-syntax"


def test_prompt13_components_do_not_consume_transport_or_reconstruct_semantics() -> None:
    component = Path("bastion_ui/components/trace/trace_topology.py").read_text()
    state = Path("bastion_ui/state/trace_topology_state.py").read_text()
    assert "generated_schemas" not in component
    assert "generated_http" not in component
    assert "dict[str" not in state
    assert "token != self.generation" in state
    assert "snapshot_id != self.selected_snapshot_id" in state
    assert "address_participates_in_transaction" not in component
    assert "TRACE_PRIVACY_CANARY_NEVER_BROWSER" not in component + state


def test_prompt13_routes_and_scenarios_have_canonical_ownership() -> None:
    assert ROUTE_BY_ID["trace.history"].path == "/trace/[report_id]/history/[snapshot_id]"
    assert ROUTE_BY_ID["trace.report"].http_operations == (
        "get_trace_graph_history_api_v1_trace_report__report_id__graph_history_get",
        "get_exact_trace_graph_snapshot",
        "get_current_trace_disagreement",
    )
    assert ROUTE_BY_ID["trace.history"].http_operations == (
        "get_exact_trace_graph_snapshot",
        "get_historical_trace_disagreement",
    )
    assert all(item.provenance is ProvenanceState.DEMO_FIXTURE for item in PROMPT13_SCENARIOS)
