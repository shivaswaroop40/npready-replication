#!/usr/bin/env bash
# Restart every Online Boutique workload (datastore first) and wait until the app answers.
# Used at the start of every run so each condition starts from fresh pods and connections.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/../common.sh"
pb_init "$HERE" restart

pb_restart_tiers "$READY_TIMEOUT" "deploy/redis-cart" "REST"
pb_wait_http_ok "$TP_URL" "$READY_TIMEOUT"
pb_state_json
