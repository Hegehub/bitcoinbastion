"""Canonical request construction for Bastion PoP V1.

Path handling preserves the ASGI-visible path. It rejects malformed paths but does
not collapse repeated slashes or percent-encoding because those distinctions may
be route/security relevant behind FastAPI or a reverse proxy.
"""

from __future__ import annotations

import hashlib
import re
from urllib.parse import parse_qsl, quote

POP_PROTOCOL_VERSION = "BASTION-POP-V1"
_ALLOWED_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"})
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")


class CanonicalRequestError(ValueError):
    """Safe canonical request error."""


def normalize_http_method(method: str) -> str:
    normalized = method.strip().upper()
    if normalized not in _ALLOWED_METHODS:
        raise CanonicalRequestError("invalid_canonical_request")
    return normalized


def normalize_request_path(path: str) -> str:
    if not isinstance(path, str) or not path.startswith("/") or _CONTROL_RE.search(path):
        raise CanonicalRequestError("invalid_canonical_request")
    return path


def canonicalize_query_string(query_string: str | bytes | None) -> str:
    if query_string in (None, b"", ""):
        return ""
    if isinstance(query_string, bytes):
        query_text = query_string.decode("utf-8", errors="strict")
    elif isinstance(query_string, str):
        query_text = query_string
    else:
        raise CanonicalRequestError("invalid_canonical_request")
    if _CONTROL_RE.search(query_text) or len(query_text) > 8192:
        raise CanonicalRequestError("invalid_canonical_request")
    pairs = parse_qsl(query_text, keep_blank_values=True, strict_parsing=False, encoding="utf-8", errors="strict")
    encoded_pairs = [(_pct(key), _pct(value)) for key, value in pairs]
    encoded_pairs.sort(key=lambda item: (item[0], item[1]))
    return "&".join(f"{key}={value}" for key, value in encoded_pairs)


def compute_body_sha256_hex(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def build_pop_canonical_request(
    *,
    method: str,
    path: str,
    query_string: str | bytes | None,
    body_hash_hex: str,
    timestamp: str,
    nonce: str,
    session_binding: str,
    protocol_version: str = POP_PROTOCOL_VERSION,
) -> str:
    method_text = normalize_http_method(method)
    path_text = normalize_request_path(path)
    query_text = canonicalize_query_string(query_string)
    body_hash = _normalize_body_hash(body_hash_hex)
    if not timestamp.isdecimal() or not nonce or _CONTROL_RE.search(nonce) or not session_binding:
        raise CanonicalRequestError("invalid_canonical_request")
    return "\n".join((protocol_version, method_text, path_text, query_text, body_hash, timestamp, nonce, session_binding))


def compute_pop_request_digest(canonical_request: str) -> str:
    return hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()


def _normalize_body_hash(body_hash_hex: str) -> str:
    value = body_hash_hex.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise CanonicalRequestError("invalid_body_hash")
    return value


def _pct(value: str) -> str:
    return quote(value, safe="-._~")
