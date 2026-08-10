from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend" / "bastion_ui"
OUTPUT = ROOT / "docs" / "frontend" / "migration" / "02_TRANSFORMATION_INVENTORY.json"
PATTERN = re.compile(r"dict\[str, Any\]|response\.json\(|\.json\(\)")


def main() -> None:
    records: list[dict[str, object]] = []
    for path in sorted(FRONTEND.rglob("*.py")):
        if path.name.startswith("generated_") or "tests" in path.parts:
            continue
        for line_number, line in enumerate(path.read_text().splitlines(), 1):
            if not PATTERN.search(line):
                continue
            relative = path.relative_to(ROOT).as_posix()
            domain = path.stem.replace("_state", "").split("_")[0].title()
            records.append(
                {
                    "id": f"P2-TX-{len(records) + 1:04d}",
                    "file": relative,
                    "line": line_number,
                    "domain": domain,
                    "consumer": path.stem,
                    "state": "RAW",
                    "risk": "Untyped payload may cross the browser-State boundary.",
                    "future_owner": f"{domain} domain adapter",
                    "migration_status": "INVENTORIED_NOT_MIGRATED",
                }
            )
    OUTPUT.write_text(json.dumps({"count": len(records), "records": records}, indent=2) + "\n")


if __name__ == "__main__":
    main()
