#!/usr/bin/env bash
# Restart every Bank of Anthos workload (databases first; they re-seed the demo data from
# emptyDir), refresh the session cookie, and wait until /home answers 200.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/../common.sh"
pb_init "$HERE" restart

pb_restart_tiers "$READY_TIMEOUT" "sts/accounts-db sts/ledger-db" "REST"
session=$("$APP_DIR/session.sh")
pb_state_json session:="$session"
