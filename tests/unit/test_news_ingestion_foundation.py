from datetime import UTC, datetime

from app.services.intelligence.news_ingestion.article_normalizer import ensure_utc
from app.services.intelligence.news_ingestion.dedup_precheck import is_duplicate_candidate
from app.services.intelligence.news_ingestion.feed_parser import parse_feed
from app.services.intelligence.news_ingestion.html_cleaner import clean_html
from app.services.intelligence.news_ingestion.retry_policy import is_retryable_status
from app.services.intelligence.news_ingestion.url_canonicalizer import canonicalize_url


def test_rss_parsing() -> None:
    xml = "<rss><channel><item><title>T</title><link>https://a.com/x?utm_source=z</link><description><p>Hi</p></description></item></channel></rss>"
    items = parse_feed(xml)
    assert len(items) == 1


def test_atom_parsing() -> None:
    atom = "<feed xmlns='http://www.w3.org/2005/Atom'><entry><title>A</title><link href='https://a.com'/></entry></feed>"
    items = parse_feed(atom)
    assert len(items) == 1


def test_canonical_url_generation() -> None:
    assert canonicalize_url("HTTPS://A.com/x/?utm_source=x&fbclid=y#frag") == "https://a.com/x"


def test_duplicate_precheck() -> None:
    assert is_duplicate_candidate(existing_canonical=True, existing_content=False, existing_title=False)[0] is True


def test_content_cleaning() -> None:
    assert "alert(1)" not in clean_html("<script>alert(1)</script><p>Hello</p>")


def test_utc_normalization() -> None:
    dt = datetime(2026, 1, 1)
    assert ensure_utc(dt).tzinfo == UTC


def test_retry_policy() -> None:
    assert is_retryable_status(429)
    assert not is_retryable_status(404)
