#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runtime_profile_lib import detect_environment, json_dumps, print_detection  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Detect a recommended Bitcoin Bastion runtime profile.")
    parser.add_argument("--json", action="store_true", help="Print stable JSON output.")
    parser.add_argument("--verbose", action="store_true", help="Print additional environment details.")
    args = parser.parse_args(argv)
    result = detect_environment()
    if args.json:
        print(json_dumps(result))
    else:
        print_detection(result, verbose=args.verbose)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
