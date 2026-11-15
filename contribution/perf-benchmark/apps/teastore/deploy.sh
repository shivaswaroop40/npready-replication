#!/usr/bin/env bash
# Deploy TeaStore (ribbon) into APP_NS from manifest.yaml. Idempotent. No post-apply steps.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/../common.sh"
pb_init "$HERE" deploy

pb_ensure_ns
pb_apply "$APP_DIR/manifest.yaml"
pb_apply "$APP_DIR/steady-configmap.yaml"
pb_wait_all "$READY_TIMEOUT"
# The pods have no readiness probes; the product page answers 200 only once the registry,
# persistence (database generated) and image/recommender services are up.
pb_wait_http_ok "$TP_URL" "$READY_TIMEOUT"
pb_state_json
