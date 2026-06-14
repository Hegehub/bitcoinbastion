from app.events.registry import EVENT_REGISTRY
from app.events.safety import SafetyFlag
from app.events.types import EventDomain


def event_catalog() -> list[dict[str, object]]:
    """Return registry metadata suitable for API, SDK, and documentation generation."""
    return [
        metadata.model_dump(mode="json")
        for _, metadata in sorted(EVENT_REGISTRY.items(), key=lambda item: item[0].value)
    ]


def event_domain_catalog() -> list[str]:
    return [domain.value for domain in EventDomain]


def safety_flag_catalog() -> list[str]:
    return [flag.value for flag in SafetyFlag]
