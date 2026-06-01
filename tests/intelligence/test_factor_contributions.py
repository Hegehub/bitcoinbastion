from app.services.intelligence.confidence.confidence_contributions import build_contributions


def test_factor_contributions_sum_entries() -> None:
    out = build_contributions({"a": (0.5, 0.2), "b": (1.0, 0.3)})
    assert len(out) == 2
    assert out[0]["contribution"] == 0.1
