def status(last_report_at: str | None, sources_count: int) -> dict[str, object]:
    return {
        "trace_module_status": "baseline_active",
        "trace_baseline_mode": True,
        "trace_sources_count": sources_count,
        "trace_external_sources_enabled": False,
        "trace_local_only_supported": True,
        "trace_last_report_at": last_report_at,
        "trace_known_limitations": ["baseline_weights", "source_calibration_pending"],
        "trace_production_calibrated": False,
    }
