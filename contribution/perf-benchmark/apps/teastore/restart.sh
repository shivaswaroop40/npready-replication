#!/usr/bin/env bash
# Restart every TeaStore workload: database and registry, then persistence, then the rest;
# wait until the product page answers.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/../common.sh"
pb_init "$HERE" restart

pb_restart_tiers "$READY_TIMEOUT" "deploy/teastore-db deploy/teastore-registry" "deploy/teastore-persistence" "REST"
pb_wait_http_ok "$TP_URL" "$READY_TIMEOUT"
pb_state_json
