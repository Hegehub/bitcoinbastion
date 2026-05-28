from app.services.intelligence.news_scoring.confidence_engine import compute_confidence


def test_confidence_bounds() -> None:
    c = compute_confidence(0.8, 0.7, 0.6, 1.0, 1.0, 0.9)
    assert 0.0 <= c <= 1.0
