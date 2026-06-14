from __future__ import annotations


def build_headers(api_key: str | None = None, headers: dict[str, str] | None = None) -> dict[str, str]:
    merged = dict(headers or {})
    if api_key:
        merged["Authorization"] = f"Bearer {api_key}"
    return merged
