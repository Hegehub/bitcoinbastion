from app.schemas.public_site import PublicRoadmapResponse


def get_roadmap() -> PublicRoadmapResponse:
    return PublicRoadmapResponse(
        current_phase="Backend presentation foundation",
        implemented=["Backend", "Trace", "Integrations", "Observability"],
        baseline=["Privacy", "Enterprise", "Calibration"],
        placeholder=["Frontend contracts evolution", "Enterprise enforcement integrations"],
        planned=["Frontend", "Operations hardening"],
        not_started=["Website UI"],
    )
