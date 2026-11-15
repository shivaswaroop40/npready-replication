#!/usr/bin/env bash
# Deploy the OpenTelemetry demo (1.12.0 manifest) into APP_NS from manifest.yaml. Idempotent.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/../common.sh"
pb_init "$HERE" deploy

pb_ensure_ns
pb_apply "$APP_DIR/manifest.yaml"
pb_apply "$APP_DIR/steady-configmap.yaml"
# Thesis post-apply step (spec section 5, enforce_missing_three.sh:29-43): observability stack,
# front proxy and shipped load generator at 0. manifest.yaml already says 0, so these are no-ops.
for d in grafana jaeger prometheus-server frontendproxy loadgenerator; do
  kc scale deploy "opentelemetry-demo-$d" --replicas=0 >/dev/null
done
kc scale sts otel-demo-opensearch --replicas=0 >/dev/null
pb_wait_all "$READY_TIMEOUT"
pb_wait_http_ok "$TP_URL" "$READY_TIMEOUT"
pb_state_json
