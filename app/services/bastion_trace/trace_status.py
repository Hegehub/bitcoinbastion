def make_status(*, reports_count: int, lite_checks_count: int, batches_count: int, source_count: int, last_report_at: str | None) -> dict[str, object]:
    return {
        "trace_module_status": "baseline",
        "trace_baseline_mode": True,
        "trace_reports_count": reports_count,
        "trace_lite_checks_count": lite_checks_count,
        "trace_batches_count": batches_count,
        "trace_review_open_count": 0,
        "trace_watchtower_active_count": 0,
        "trace_source_count": source_count,
        "trace_stale_source_count": 0,
        "trace_last_report_at": last_report_at,
        "trace_external_sources_enabled": False,
        "trace_local_only_supported": True,
        "trace_production_calibrated": False,
        "trace_known_limitations": ["baseline_metrics", "calibration_pending"],
    }
