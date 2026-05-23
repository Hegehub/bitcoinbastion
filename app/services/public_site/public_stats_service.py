def get_public_stats() -> dict[str, object]:
    return {
        "reports_generated": 0,
        "proof_packets_generated": 0,
        "watchtower_entries": 0,
        "runtime_events": 0,
        "supported_modules": ["trace", "citadel", "treasury", "observability"],
        "limitations": ["Aggregate baseline counters only"],
    }
