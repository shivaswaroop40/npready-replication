#!/usr/bin/env bash
# Restart every running OpenTelemetry demo workload (broker, cache, flag service and collector
# first) and wait until the recommendations API answers.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/../common.sh"
pb_init "$HERE" restart

pb_restart_tiers "$READY_TIMEOUT" \
  "deploy/opentelemetry-demo-kafka deploy/opentelemetry-demo-valkey deploy/opentelemetry-demo-flagd deploy/opentelemetry-demo-otelcol" \
  "REST"
pb_wait_http_ok "$TP_URL" "$READY_TIMEOUT"
pb_state_json
