import re


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def safe_lower(value: str) -> str:
    return normalize_whitespace(value).lower()


def normalize_title(title: str) -> str:
    return safe_lower(title)
