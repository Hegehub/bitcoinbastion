from app.schemas.public_site import PublicFeatureAvailability, PublicFeatureEntry, PublicFeatureStatus


def list_features() -> list[PublicFeatureEntry]:
    entries = [
        ("trace-lite", "Lite Address Check"),
        ("trace-replay", "Trace Replay"),
        ("trace-proof", "Proof Packets"),
        ("trace-privacy", "Privacy Shield"),
        ("trace-counterparty", "Counterparty Lens"),
        ("trace-watchtower", "Watchtower"),
        ("trace-batch", "Batch Screening"),
        ("trace-review-desk", "Review Desk"),
        ("trace-enterprise", "Enterprise Governance"),
        ("trace-metrics", "Observability Metrics"),
        ("trace-telegram", "Telegram Commands"),
    ]
    return [
        PublicFeatureEntry(
            id=i,
            name=n,
            category="Trace",
            summary="Baseline capability in Bastion Trace presentation layer.",
            status=PublicFeatureStatus.BASELINE,
            availability=PublicFeatureAvailability.PUBLIC if i == "trace-lite" else PublicFeatureAvailability.INTERNAL,
            safety_notes=["Advisory-only", "No-custody"],
            limitations=["Not production-calibrated"],
        )
        for i, n in entries
    ]
