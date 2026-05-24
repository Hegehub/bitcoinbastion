from datetime import UTC, datetime


def get_public_status() -> dict[str, object]:
    return {
        "platform_status": "baseline",
        "trace_status": "baseline",
        "production_calibrated": False,
        "modules": {
            "trace": "baseline",
            "citadel": "baseline",
            "treasury": "baseline",
            "register": "baseline_placeholder",
            "observability": "baseline",
        },
        "known_limitations": [
            "Public APIs are presentation-safe abstractions.",
            "Public APIs are advisory-only.",
            "No production calibration evidence yet.",
        ],
        "last_update": datetime.now(UTC),
    }
