from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

TRACKING_KEYS = {"fbclid", "gclid"}


def canonicalize_url(url: str) -> str:
    p = urlparse(url.strip())
    query = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if not (k.lower().startswith("utm_") or k.lower() in TRACKING_KEYS)]
    path = "/".join(x for x in p.path.split("/") if x)
    norm_path = f"/{path}" if path else "/"
    return urlunparse((p.scheme.lower(), p.netloc.lower(), norm_path.rstrip("/") or "/", "", urlencode(query), ""))
