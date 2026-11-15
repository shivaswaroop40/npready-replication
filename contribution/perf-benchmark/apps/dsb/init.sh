#!/usr/bin/env bash
# Populate the social network exactly as the thesis did: the shipped init_social_graph.py on
# socfb-Reed98 with --compose (962 users, follows, posts), run by dsb-init-job.yaml (verbatim
# thesis file). The mongodb/redis pods have no volumes, so every datastore restart empties them.
# The datastore pods and their restart counts at the end of a successful init are recorded in
# ConfigMap perfbench-dsb-init; init is skipped while that record still matches (idempotent).
# Usage: init.sh [--force]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/../common.sh"
pb_init "$HERE" init

stores() {
  kc get pods -o json | jq -r '[.items[] | select(.status.phase == "Running")
    | select(.metadata.name | test("-(mongodb|redis|memcached)-"))
    | .metadata.name + ":" + ([.status.containerStatuses[]?.restartCount] | add // 0 | tostring)]
    | sort | join(",")'
}

now=$(stores)
[ -n "$now" ] || pb_die "no running datastore pods"
was=$(kc get cm perfbench-dsb-init -o jsonpath='{.data.stores}' 2>/dev/null || true)
if [ "${1:-}" != "--force" ] && [ "$now" = "$was" ]; then
  pb_log "social graph already initialised for these datastore pods; skipping"
  jq -cn --arg app "$APP" '{app: $app, step: "init", ok: true, skipped: true}'
  exit 0
fi

# empty_stores: restart every datastore Deployment (no volumes, so they come back empty)
empty_stores() {
  local ds
  ds=$(pb_workloads | grep -E -- '-(mongodb|redis|memcached)$' | tr '\n' ' ')
  # shellcheck disable=SC2086
  for w in $ds; do kc rollout restart "$w" >/dev/null; done
  # shellcheck disable=SC2086
  pb_wait_rollouts "$READY_TIMEOUT" $ds
  pb_wait_no_terminating "$READY_TIMEOUT"
}

# A rebuild (a datastore was replaced since the last init, or --force) starts from empty
# datastores, so the graph is never built on top of what is left of the old one.
if [ -n "$was" ]; then
  pb_log "rebuilding the social graph: emptying every datastore first"
  empty_stores
fi

summary=""
for attempt in 1 2; do
  kc delete job dsb-init --ignore-not-found --wait=true >/dev/null
  if [ "$attempt" = 1 ]; then
    pb_apply "$APP_DIR/dsb-init-job.yaml"          # verbatim thesis job (200 connections at once)
  else
    # The first attempt lost a datastore (the chart's 128Mi Mongo limit: with 200 simultaneous
    # requests the services open many Mongo connections). Empty every datastore so the retry
    # starts from a clean slate (a partial first graph would leave duplicate follows and posts),
    # then run the same job paced to 50 connections (init_social_graph.py --limit 50). The graph
    # it builds is the same as a clean single run.
    empty_stores
    kubectl create --dry-run=client -o json -f "$APP_DIR/dsb-init-job.yaml" \
      | jq -s '{apiVersion: "v1", kind: "List", items: [.[] | if .kind == "List" then .items[] else . end
               | if .kind == "Job" then .spec.template.spec.containers[0].args[0] |= sub("--compose"; "--compose --limit 50") else . end]}' \
      | kc apply -f - >/dev/null || pb_die "cannot apply the paced init job"
    pb_log "init attempt $attempt: datastores emptied, job paced (init_social_graph.py --limit 50)"
  fi
  before=$(stores)
  aborted=0
  dl=$(pb_deadline "$INIT_TIMEOUT")
  while :; do
    st=$(kc get job dsb-init -o jsonpath='{.status.succeeded}/{.status.failed}')
    if [ "${st%/*}" = 1 ]; then break; fi
    if [ -n "${st#*/}" ] && [ "${st#*/}" != 0 ]; then
      pb_die "dsb-init failed: $(kc logs job/dsb-init --tail=20 2>&1 | tr '\n' ' ')"
    fi
    # a datastore restarted mid-init: this attempt's graph is incomplete, stop it now
    if [ "$(stores)" != "$before" ]; then aborted=1; break; fi
    [ "$(date +%s)" -lt "$dl" ] || pb_die "dsb-init not done after ${INIT_TIMEOUT}s"
    sleep 10
  done
  if [ "$aborted" = 0 ]; then
    summary=$(kc logs job/dsb-init 2>/dev/null | grep -E '^(Succeeded|Failed):' | tr '\n' ' ' | cut -c1-400)
    if [ "$before" = "$(stores)" ]; then
      pb_log "init attempt $attempt done: $summary"
      break
    fi
  fi
  if [ "$attempt" = 2 ]; then pb_die "datastores restarted during both init attempts"; fi
  pb_log "datastore restarted during init attempt $attempt ($before -> $(stores)); retrying"
  kc delete job dsb-init --ignore-not-found --wait=true >/dev/null
done

kc create configmap perfbench-dsb-init --from-literal=stores="$(stores)" --dry-run=client -o yaml \
  | kc apply -f - >/dev/null
jq -cn --arg app "$APP" --argjson attempts "$attempt" --arg result "$summary" \
  --argjson secs $(( $(date +%s) - PB_T0 )) \
  '{app: $app, step: "init", ok: true, skipped: false, attempts: $attempts, result: $result, seconds: $secs}'
