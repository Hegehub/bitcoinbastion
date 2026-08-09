from scripts.analyze_http_generation_preflight import build_report


def test_full_generation_preflight_is_fail_closed_and_complete() -> None:
    report = build_report()
    counts = report["counts"]

    assert counts == {
        "runtime_http": 369,
        "generation_candidates": 194,
        "protected_candidates": 0,
        "mutation_candidates": 0,
        "protected_only": 0,
        "mutation_only": 0,
        "protected_mutations": 0,
        "b01_b02_unique_operations": 0,
        "ready": 194,
        "security_blocked": 0,
        "mutation_blocked": 0,
        "security_deferred": 65,
        "mutation_deferred": 65,
        "schema_capabilities_unproven": 2,
    }
    assert report["unproven_schema_capabilities"] == ["additionalProperties", "anyOf"]
    assert report["response_vocabulary"] == {
        "media_types": {"application/json": 194},
        "success_statuses": {"200": 194},
    }
    assert report["blockers"] == []
    assert report["html_operations"] == []
    assert len(report["deferred_no_content_operations"]) == 4
    assert report["websocket_authority"].startswith("DEFERRED_TO_PROMPT_4")
