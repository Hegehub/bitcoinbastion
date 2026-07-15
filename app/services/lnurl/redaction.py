"""LNURL redaction and stable fingerprint helpers."""
from __future__ import annotations
import hashlib
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

SENSITIVE_QUERY_KEYS = frozenset({
    "k1", "sig", "key", "pr", "preimage", "payerdata", "payerData", "auth", "nonce", "token",
    "session", "session_token", "access_pass", "payment_secret", "withdraw_id",
})

def _fingerprint(prefix: str, value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8', 'surrogatepass')).hexdigest()}"

def fingerprint_lnurl_value(value: str) -> str:
    return _fingerprint("lnurl", value)

def fingerprint_lnurl_url(url: str) -> str:
    return _fingerprint("url", url)

def redact_lnurl_url(url: str) -> str:
    try:
        p = urlsplit(url)
        host = (p.hostname or "").lower()
        netloc = host
        if p.port:
            netloc = f"{netloc}:{p.port}"
        pairs = parse_qsl(p.query, keep_blank_values=True)
        safe = [(k, "[REDACTED]" if k in SENSITIVE_QUERY_KEYS or k.lower() in SENSITIVE_QUERY_KEYS else v[:16]) for k, v in pairs]
        return urlunsplit((p.scheme.lower(), netloc, p.path or "/", urlencode(safe), ""))
    except Exception:
        return f"[REDACTED-LNURL:{fingerprint_lnurl_url(url)[:19]}]"

def redact_lnurl_value(value: str) -> str:
    if value.lower().startswith(("lnurl1", "lightning:lnurl1")):
        return f"[REDACTED-LNURL:{fingerprint_lnurl_value(value)[:19]}]"
    return redact_lnurl_url(value)
