#!/usr/bin/env bash
# Restart the stateless DeathStarBench workloads before a run: jaeger and every service first,
# then the two OpenResty front ends (nginx-thrift last, so its connection pools open against the
# new pods; the thesis restarted nginx-thrift before journey A for the same reason).
# The datastores (every *-mongodb, *-redis and *-memcached Deployment) keep running: they have no
# volumes, so a restart would empty them and force the 9,424-post social-graph init again (over
# 15 minutes here). The graph is built once, by deploy.sh, as in the thesis. init.sh (without
# --force) then only checks that no datastore pod was replaced or restarted since that init; if
# one was, it rebuilds the graph before the run, so every run reads the same graph.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/../common.sh"
pb_init "$HERE" restart

PB_RESTART_KEEP=$(pb_workloads | grep -E -- '-(mongodb|redis|memcached)$' | tr '\n' ' ')
[ -n "$PB_RESTART_KEEP" ] || pb_die "no datastore workloads found"
export PB_RESTART_KEEP
pb_restart_tiers "$READY_TIMEOUT" "REST" "deploy/media-frontend" "deploy/nginx-thrift"
pb_wait_http_ok http://nginx-thrift:8080/ "$READY_TIMEOUT"
init=$("$APP_DIR/init.sh")
pb_wait_http_ok "$TP_URL" "$READY_TIMEOUT"
pb_state_json kept:="$(printf '%s\n' $PB_RESTART_KEEP | jq -Rsc 'split("\n") | map(select(length > 0))')" init:="$init"
