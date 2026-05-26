import hashlib
import re
import unicodedata

from app.services.news.deduplication.canonicalization import normalize_url


def hash_url(url: str) -> str:
    return hashlib.sha256(normalize_url(url).encode("utf-8")).hexdigest()


def normalize_title(title: str) -> str:
    t = unicodedata.normalize("NFKC", title).lower()
    t = "".join(ch for ch in t if ch.isascii())
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def hash_title(title: str) -> str:
    return hashlib.sha256(normalize_title(title).encode("utf-8")).hexdigest()


def hash_content(content: str) -> str:
    text = re.sub(r"<[^>]+>", " ", content)
    text = re.sub(r"\s+", " ", text).strip()[:20000]
    return hashlib.sha256(text.lower().encode("utf-8")).hexdigest()
