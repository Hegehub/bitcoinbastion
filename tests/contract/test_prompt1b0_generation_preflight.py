from scripts.analyze_http_generation_preflight import build_report


def test_full_generation_preflight_is_fail_closed_and_complete() -> None:
    report = build_report()
    counts = report["counts"]

    assert counts == {
        "runtime_http": 369,
        "generation_candidates": 309,
        "protected_candidates": 65,
        "mutation_candidates": 65,
        "ready": 200,
        "security_blocked": 65,
        "mutation_blocked": 65,
        "schema_capabilities_unproven": 2,
    }
    assert report["unproven_schema_capabilities"] == ["additionalProperties", "anyOf"]
    assert report["response_vocabulary"] == {
        "media_types": {"application/json": 300, "no-content": 3, "text/html": 6},
        "success_statuses": {"200": 305, "201": 1, "204": 3},
    }
    assert all(row["blocker"] in {"P1B0-B01", "P1B0-B02"} for row in report["blockers"])
    assert report["websocket_authority"].startswith("DEFERRED_TO_PROMPT_4")
