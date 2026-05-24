#!/usr/bin/env bash
set -euo pipefail
grep -qi "allowed changes" docs/RC_FREEZE.md
grep -qi "disallowed" docs/RC_FREEZE.md
echo "rc freeze policy baseline present"
