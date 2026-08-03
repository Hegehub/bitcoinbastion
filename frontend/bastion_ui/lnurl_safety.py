from __future__ import annotations

from urllib.parse import urlsplit

_SECRET_QUERY_KEYS = {
    "access_pass",
    "session",
    "session_token",
    "recovery",
    "private_key",
    "signature",
}


def validate_success_action_url(url: str, *, allowed_domains: frozenset[str]) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("unsafe_success_action_url")
    if parsed.hostname.casefold() not in {domain.casefold() for domain in allowed_domains}:
        raise ValueError("unapproved_success_action_domain")
    query_keys = {part.partition("=")[0].casefold() for part in parsed.query.split("&") if part}
    if query_keys & _SECRET_QUERY_KEYS:
        raise ValueError("sensitive_success_action_url")
    return url


def validate_payment_comment(comment: str, comment_allowed: int) -> str:
    if comment_allowed < 0 or len(comment) > comment_allowed:
        raise ValueError("comment_exceeds_backend_limit")
    return comment
