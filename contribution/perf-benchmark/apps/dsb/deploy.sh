#!/usr/bin/env bash
# Deploy DeathStarBench socialNetwork into APP_NS from manifest.yaml, then initialise the
# social graph once (thesis post-apply step). Idempotent.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/../common.sh"
pb_init "$HERE" deploy

# the OpenResty init containers read the pinned fork files from a hostPath on the workers
src=$("$APP_DIR/dsb_src.sh")
pb_ensure_ns
pb_apply "$APP_DIR/manifest.yaml"
pb_apply "$APP_DIR/steady-configmap.yaml"
pb_wait_all "$READY_TIMEOUT"
# nginx-thrift serves its static pages on /; the timeline read is checked after init
pb_wait_http_ok http://nginx-thrift:8080/ "$READY_TIMEOUT"
init=$("$APP_DIR/init.sh")
pb_wait_http_ok "$TP_URL" "$READY_TIMEOUT"
pb_state_json src:="$src" init:="$init"
