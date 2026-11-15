#!/usr/bin/env bash
# Deploy Online Boutique v0.10.6 into APP_NS from manifest.yaml. Idempotent.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/../common.sh"
pb_init "$HERE" deploy

pb_ensure_ns
pb_apply "$APP_DIR/manifest.yaml"
# Thesis post-apply step (spec section 5, boutique_capture.sh:36-42): the shipped generator
# stays at 0; journey A now runs as the pb-steady Job. manifest.yaml already says 0.
kc scale deploy/loadgenerator --replicas=0 >/dev/null
pb_wait_all "$READY_TIMEOUT"
pb_wait_http_ok "$TP_URL" "$READY_TIMEOUT"
pb_state_json
