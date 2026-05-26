from urllib.parse import urlparse, urlunparse


def normalize_url(url: str) -> str:
    return url.strip()


def canonicalize_url(url: str) -> str:
    parsed = urlparse(normalize_url(url))
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/") or "/"
    return urlunparse((scheme, netloc, path, "", parsed.query, ""))


def validate_http_url(url: str) -> str:
    parsed = urlparse(normalize_url(url))
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL must be valid HTTP(S) URL")
    return url
