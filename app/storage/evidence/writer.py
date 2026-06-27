"""Deterministic JSON writer and redaction helpers for storage evidence."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from app.storage.evidence.models import EvidenceWriteResult, StorageEvidence

DEFAULT_STORAGE_EVIDENCE_DIR = Path("artifacts/storage")
REDACTED = "[REDACTED]"
SENSITIVE_KEY_TERMS = (
    "secret",
    "token",
    "password",
    "private",
    "xprv",
    "yprv",
    "zprv",
    "seed",
    "mnemonic",
    "access_key",
    "secret_key",
    "authorization",
    "cookie",
)
SENSITIVE_VALUE_TERMS = (
    "seed phrase",
    "private key",
    "wallet.dat",
    "xprv",
    "yprv",
    "zprv",
    "mnemonic",
    "bearer ",
)


def redact_evidence_value(value: Any) -> Any:
    """Recursively redact sensitive keys and obvious sensitive string values."""

    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if _is_sensitive_key(key_text):
                redacted[key_text] = REDACTED
            else:
                redacted[key_text] = redact_evidence_value(item)
        return redacted
    if isinstance(value, list):
        return [redact_evidence_value(item) for item in value]
    if isinstance(value, tuple):
        return [redact_evidence_value(item) for item in value]
    if isinstance(value, str) and _is_sensitive_value(value):
        return REDACTED
    return value


def write_evidence_json(
    evidence: StorageEvidence,
    filename: str,
    output_dir: Path | str = DEFAULT_STORAGE_EVIDENCE_DIR,
) -> EvidenceWriteResult:
    """Write deterministic UTF-8 evidence JSON and return file metadata."""

    safe_filename = _safe_filename(filename)
    output_path = Path(output_dir) / safe_filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = redact_evidence_value(evidence.model_dump(mode="json"))
    rendered = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    output_path.write_text(rendered, encoding="utf-8")
    raw = output_path.read_bytes()
    return EvidenceWriteResult(
        path=str(output_path),
        sha256=sha256(raw).hexdigest(),
        size_bytes=len(raw),
    )


def _safe_filename(filename: str) -> str:
    if not filename or not filename.strip():
        raise ValueError("Evidence filename must not be empty.")
    candidate = filename.strip()
    if "/" in candidate or "\\" in candidate or candidate in {".", ".."}:
        raise ValueError("Evidence filename must be a simple file name.")
    if not candidate.endswith(".json"):
        raise ValueError("Evidence filename must end with .json.")
    return candidate


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(term in lowered for term in SENSITIVE_KEY_TERMS)


def _is_sensitive_value(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in SENSITIVE_VALUE_TERMS)
