#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runtime_profile_lib import (  # noqa: E402
    EXIT_INVALID_USAGE,
    EXIT_MISSING_FILE,
    build_plan,
    json_dumps,
    plan_to_dict,
    print_plan,
    validate_plan,
    apply_plan,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render or execute a Bitcoin Bastion runtime profile plan.")
    parser.add_argument("--profile", required=True, help="Runtime profile name.")
    parser.add_argument("--env", required=True, help="Environment: local, dev, staging, production.")
    parser.add_argument("--dry-run", action="store_true", help="Print the command plan without executing apply commands. Default.")
    parser.add_argument("--validate", action="store_true", help="Run the safe validation command for the selected profile.")
    parser.add_argument("--apply", action="store_true", help="Apply the selected profile. Requires --yes.")
    parser.add_argument("--yes", action="store_true", help="Explicit operator confirmation for apply mode.")
    parser.add_argument("--json", action="store_true", help="Print the command plan as JSON.")
    args = parser.parse_args(argv)

    if args.apply and not args.yes:
        print("Refusing to apply without --yes. Dry-run is the default.", file=sys.stderr)
        return EXIT_INVALID_USAGE
    if args.apply and args.validate:
        print("Choose either --validate or --apply, not both.", file=sys.stderr)
        return EXIT_INVALID_USAGE

    mode = "apply" if args.apply else "validate" if args.validate else "dry-run"
    try:
        plan = build_plan(args.profile, args.env, mode=mode)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_INVALID_USAGE
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_MISSING_FILE

    if args.json:
        print(json_dumps(plan_to_dict(plan)))
    else:
        print_plan(plan)

    if args.validate:
        return validate_plan(plan)
    if args.apply:
        return apply_plan(plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
