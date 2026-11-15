#!/usr/bin/env bash
# Delete the app (namespace and any cluster-scoped objects of manifest.yaml) and wait.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/../common.sh"
pb_init "$HERE" undeploy

kc delete -f "$APP_DIR/manifest.yaml" --ignore-not-found --wait=false >/dev/null 2>&1 || true
kubectl delete namespace "$APP_NS" --ignore-not-found --timeout="${READY_TIMEOUT}s" >/dev/null
pb_log "namespace $APP_NS gone"
printf '{"app":"%s","ns":"%s","step":"undeploy","ok":true,"seconds":%d}\n' "$APP" "$APP_NS" $(( $(date +%s) - PB_T0 ))
