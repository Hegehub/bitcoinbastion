import json
from pathlib import Path

from scripts.analyze_http_generation_preflight import build_report

ROOT = Path(__file__).resolve().parents[2]
OWNERSHIP = ROOT / "docs/frontend/migration/01_HTTP_CLIENT_OWNERSHIP_INPUT.json"


def test_full_generation_preflight_is_fail_closed_and_complete() -> None:
    report = build_report()
    counts = report["counts"]

    assert counts["runtime_http"] >= counts["generation_candidates"]
    ownership = json.loads(OWNERSHIP.read_text())
    assert counts["generation_candidates"] == len(ownership["authoritative_http_operations"])
    assert counts["ready"] + counts["b01_b02_unique_operations"] == counts["generation_candidates"]
    assert counts["protected_candidates"] == counts["protected_only"]
    assert counts["mutation_candidates"] == counts["mutation_only"]
    # This is the raw fail-closed preflight. Reviewed Stage-1 overrides are
    # validated by generate_http_transport.py --check and semantic handoff.
    assert {item["operation_id"] for item in report["blockers"]} == {
        "create_access_checkout_api_v1_access_checkouts_post",
        "create_issuance_challenge_api_v1_access_issuance_challenges_post",
        "export_trace_evidence",
        "get_current_trace_proof_packet",
        "get_historical_trace_proof_packet",
        "get_trace_evidence_lineage",
        "jobs_api_v1_operations_jobs_get",
        "market_similarity_report",
        "issue_access_api_v1_access_issuance_post",
        "operations_get_incident",
        "operations_list_incidents",
        "operations_list_slo",
        "replay_trace_evidence",
        "submit_trace_api_v1_trace_submit_post",
        "verify_trace_evidence_identity",
    }
    assert report["unproven_schema_capabilities"] == []
    assert sum(report["response_vocabulary"]["media_types"].values()) == counts["generation_candidates"]
    assert sum(report["response_vocabulary"]["success_statuses"].values()) == counts["generation_candidates"]
    assert report["html_operations"] == []
    assert len(report["deferred_no_content_operations"]) == 4
    assert report["websocket_authority"].startswith("AUTHORITATIVE_PROMPT_4")
