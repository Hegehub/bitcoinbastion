#!/usr/bin/env python3
"""Generate the explicit non-canonical frontend literal/wrapper disposition register."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs/frontend/migration"
AUDIT = DOCS / "00_FRONTEND_URL_AUDIT.json"
OUT = DOCS / "01B1_TRANSPORT_COMPATIBILITY.json"


def render() -> str:
    audit = json.loads(AUDIT.read_text())
    matched = set(audit["matched"])
    stale = set(audit["stale_or_absent"])
    entries = []
    for literal, sources in sorted(audit["sources"].items()):
        handwritten = sorted(
            source
            for source in sources
            if source != "frontend/bastion_ui/transport/generated_http.py"
        )
        if not handwritten:
            continue
        if literal in matched:
            classification = "COMPATIBILITY_WRAPPER"
            condition = "Prompt 2 consumer migration proves generated DTO adapter parity"
        elif literal in stale:
            classification = "STALE_RUNTIME_ABSENT"
            condition = "remove only after consumer and replacement-route review"
        else:
            classification = "NON_CANONICAL_REVIEW_REQUIRED"
            condition = "resolve route identity before transport migration"
        entries.append(
            {
                "active_canonical_owner": "generated registry lookup by method/path"
                if classification == "COMPATIBILITY_WRAPPER"
                else None,
                "classification": classification,
                "consumers": handwritten,
                "literal": literal,
                "removal_condition": condition,
            }
        )
    payload = {
        "entries": entries,
        "policy": "handwritten paths are non-canonical and do not count as generated ownership",
        "source_audit": str(AUDIT.relative_to(ROOT)),
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = render()
    if args.check:
        if not OUT.exists() or OUT.read_text() != value:
            raise SystemExit("transport compatibility registry is stale")
    else:
        OUT.write_text(value)


if __name__ == "__main__":
    main()
