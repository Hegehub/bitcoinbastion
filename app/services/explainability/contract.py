from app.schemas.common import ExplainabilityContractOut


def build_explainability_contract(
    *,
    domain: str,
    confidence: float,
    freshness: dict[str, object] | None = None,
    source_type: str = "unknown",
    provider_name: str = "unknown",
    is_mock: bool = False,
    is_fallback: bool = False,
    limitations: list[str] | None = None,
    signals: dict[str, object] | None = None,
) -> dict[str, object]:
    return ExplainabilityContractOut(
        domain=domain,
        source_type=source_type,
        provider_name=provider_name,
        is_mock=is_mock,
        is_fallback=is_fallback,
        confidence=confidence,
        freshness=freshness or {},
        limitations=limitations or [],
        signals=signals or {},
    ).model_dump()
