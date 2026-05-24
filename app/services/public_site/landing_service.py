from app.services.public_site.feature_catalog import list_features
from app.services.public_site.public_safety import safety_principles
from app.services.public_site.roadmap_service import get_roadmap
from app.services.public_site.status_service import get_public_status


def get_landing() -> dict[str, object]:
    return {
        "platform_name": "Bitcoin Bastion",
        "platform_tagline": "Bitcoin-first, no-custody, advisory backend foundation",
        "modules": ["Bastion Trace", "Citadel", "Treasury", "Register", "Observability"],
        "status_summary": get_public_status(),
        "feature_catalog": [f.model_dump(mode="json") for f in list_features()],
        "roadmap_summary": get_roadmap().model_dump(mode="json"),
        "safety_principles": safety_principles(),
        "production_readiness": {"production_calibrated": False, "status": "baseline"},
        "links": {
            "public_api": "/api/v1/public",
            "trace_docs": "/docs/BASTION_TRACE.md",
        },
    }
