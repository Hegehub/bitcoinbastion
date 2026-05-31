from app.services.market_intelligence.domain.enums import NewsSourceKind
from app.services.market_intelligence.schemas.news_article import NewsArticleResponse
from app.services.market_intelligence.utils.hashing import stable_text_hash, url_hash
from app.services.market_intelligence.validation.normalization import normalize_title
from app.services.market_intelligence.validation.urls import canonicalize_url, validate_http_url


def test_url_normalization() -> None:
    assert canonicalize_url("HTTPS://Example.com/path/") == "https://example.com/path"
    assert validate_http_url("https://example.com") == "https://example.com"


def test_title_normalization() -> None:
    assert normalize_title("  Hello   BTC  ") == "hello btc"


def test_stable_hashing() -> None:
    assert stable_text_hash("Hello   BTC") == stable_text_hash("hello btc")
    assert len(url_hash("https://example.com")) == 64


def test_enum_serialization() -> None:
    assert NewsSourceKind.RSS.value == "RSS"


def test_duplicate_flags_schema() -> None:
    out = NewsArticleResponse(id=1, source_id=1, title="a", is_duplicate=True)
    assert out.is_duplicate is True
