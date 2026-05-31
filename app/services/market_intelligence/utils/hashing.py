import hashlib

from app.services.market_intelligence.validation.urls import canonicalize_url
from app.services.market_intelligence.validation.normalization import normalize_whitespace


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def stable_text_hash(value: str) -> str:
    return sha256_hex(normalize_whitespace(value).lower())


def url_hash(value: str) -> str:
    return sha256_hex(canonicalize_url(value))
