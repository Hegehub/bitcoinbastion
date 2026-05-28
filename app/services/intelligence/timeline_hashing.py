import hashlib
import json


def _stable(data: dict[str, object]) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def build_event_hash(data: dict[str, object]) -> str:
    return _stable(data)


def build_context_hash(data: dict[str, object]) -> str:
    return _stable(data)


def build_replay_hash(data: dict[str, object]) -> str:
    return _stable(data)
