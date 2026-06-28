#!/usr/bin/env bash
set -euo pipefail

cat >&2 <<'MSG'
Timescale aggregate refresh is intentionally not wired to an unauthenticated mutation endpoint.
Use app.storage.timeseries.operations.TimescaleOperationsService.refresh_all_recent()
from an authenticated operator shell or maintenance job after credentials are loaded.
MSG
exit 2
