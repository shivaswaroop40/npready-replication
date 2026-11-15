#!/usr/bin/env bash
# run_matrix.sh <app> [--reps N | --rep-list "1 2" | --cycles K | --cycle-list "1 2"] [--short]
#                     [--conds "baseline hubble hubble_agent ..."] [--retries N] [--keep] [--force-other-apps]
#
# Runs every condition for one app, for reps 1..N (or exactly the reps in --rep-list, so one
# app's matrix can be split over two plays), on cp-01 as root:
#   - takes the cluster lock (one benchmark at a time), refuses if another app's namespace
#     exists (two apps at once would skew every number) unless --force-other-apps,
#   - pre-pulls apps/<app>/images.txt on every node, deploys the app once (deploy.sh),
#   - for each rep runs the conditions in the order pb_shuffle gives for (app, rep): a balanced
#     design for the 5 conditions in reps 1-3, else a shuffle seeded with sha256("<app>:rep<r>").
#     The order depends only on app and rep, so a split matrix runs the same orders as an
#     unsplit one. It is saved to rep<r>/ORDER.json and reused on resume,
#   - skips runs that already have DONE, so it resumes after a crash or a play restart,
#   - a failing run is logged (FAILED + reason) and retried up to --retries times (default 1),
#     then the matrix moves on,
#   - each run is killed after RUN_TIMEOUT s (app.env; PB_RUN_TIMEOUT overrides; default 5400,
#     3000 for --short),
#   - keeps $PB_RESULTS/STATUS.json current (progress, mean run time, ETA) for the orchestrator,
#   - at the end undeploys the app if every run is DONE (--keep keeps it).
# Interleaved short cycles (randomized multiple interleaved trials, Abedi & Brecht, ICPE 2017):
#   --cycles K runs cycles 1..K (--cycle-list "3 4 5" exactly those, to split over plays). A cycle
#   runs every condition once with run_one.sh --profile cycle (60 s idle, 60 s warm-up, 300 s
#   window, 1 x TP_N_CYCLE requests per mode) into <app>/cycle<k>/<cond>/. The order of cycle k is
#   sequence k of a Williams design for the 5 conditions (pb_williams in lib.sh: 10 sequences,
#   every condition twice in every position, every ordered pair adjacent twice); cycles 11-20
#   reuse the set in a fresh seeded order. Saved to cycle<k>/ORDER.json and reused on resume.
#   Run watchdog: PB_RUN_TIMEOUT > RUN_TIMEOUT_CYCLE (app.env) > 2400 s; STATUS.json estimate
#   before the first run: EST_RUN_S_CYCLE (app.env) > 720 s. --short does not combine with cycles.
# Progress: /opt/perfbench/results/<app>/PROGRESS.log, /opt/perfbench/results/STATUS.json
# Start it detached, e.g.:
#   nohup setsid /opt/perfbench/bin/run_matrix.sh bank > /opt/perfbench/results/bank.matrix.out 2>&1 < /dev/null &
set -uo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export PB_ROOT=${PB_ROOT:-$(dirname "$HERE")}
# shellcheck source=lib.sh source-path=SCRIPTDIR
. "$HERE/lib.sh"

usage() { sed -n '2,3p' "$0" | sed 's/^# //' >&2; exit 2; }
[ $# -ge 1 ] || usage
APP=$1; shift
REPS=3 REP_LIST="" SHORT=0 CONDS=$PB_CONDS_ALL RETRIES=1 KEEP=0 FORCE_OTHER=0
CYCLES="" CYCLE_LIST="" REPS_SET=0
while [ $# -gt 0 ]; do
  case $1 in
    --reps) REPS=$2; REPS_SET=1; shift ;;
    --rep-list) REP_LIST=$2; shift ;;
    --cycles) CYCLES=$2; shift ;;
    --cycle-list) CYCLE_LIST=$2; shift ;;
    --short) SHORT=1 ;;
    --conds) CONDS=$2; shift ;;
    --retries) RETRIES=$2; shift ;;
    --keep) KEEP=1 ;;
    --force-other-apps) FORCE_OTHER=1 ;;
    *) usage ;;
  esac
  shift
done
[[ $REPS =~ ^[0-9]+$ ]] && [[ $RETRIES =~ ^[0-9]+$ ]] || usage
# layout: rep<r>/ (profile full or short) or cycle<k>/ (profile cycle)
if [ -n "$CYCLES$CYCLE_LIST" ]; then
  [ "$REPS_SET" = 0 ] && [ -z "$REP_LIST" ] || { echo "--cycles/--cycle-list do not combine with --reps/--rep-list" >&2; exit 2; }
  [ "$SHORT" = 0 ] || { echo "--short does not combine with --cycles (use PB_STEADY_S etc. for a quick check)" >&2; exit 2; }
  if [ -z "$CYCLE_LIST" ]; then
    [[ $CYCLES =~ ^[1-9][0-9]*$ ]] || { echo "bad --cycles '$CYCLES'" >&2; exit 2; }
    CYCLE_LIST=$(seq -s ' ' 1 "$CYCLES")
  fi
  LAYOUT=cycle PROFILE=cycle REP_LIST=$CYCLE_LIST
else
  LAYOUT=rep PROFILE=full
  [ "$SHORT" = 1 ] && PROFILE=short
  [ -n "$REP_LIST" ] || REP_LIST=$(seq -s ' ' 1 "$REPS")
fi
for r in $REP_LIST; do [[ $r =~ ^[1-9][0-9]*$ ]] || { echo "bad $LAYOUT '$r' in the $LAYOUT list" >&2; exit 2; }; done
REP_LIST=$(tr ' ' '\n' <<<"$REP_LIST" | grep -v '^$' | sort -n -u | tr '\n' ' ' | sed 's/ $//')
# canonical order before shuffling, so the --conds spelling does not change the order
SEL=""
for c in $PB_CONDS_KNOWN; do case " $CONDS " in *" $c "*) SEL+="$c " ;; esac; done
for c in $CONDS; do case " $PB_CONDS_KNOWN " in *" $c "*) ;; *) echo "unknown condition $c" >&2; exit 2 ;; esac; done
CONDS=${SEL% }
[ -n "$CONDS" ] || usage

RESDIR=$PB_RESULTS/$APP
mkdir -p "$RESDIR"
PROG=$RESDIR/PROGRESS.log
plog() { printf '%s %s\n' "$(pb_iso)" "$*" | tee -a "$PROG" >&2; }

exec 8>"$PB_LOCK"
flock -n 8 || { plog "another perfbench run holds $PB_LOCK; not starting"; exit 1; }
export PB_LOCK_HELD=1

pb_load_app "$APP" || { plog "cannot load apps/$APP"; exit 1; }
if [ -n "${PB_RUN_TIMEOUT:-}" ]; then RUN_TIMEOUT=$PB_RUN_TIMEOUT
elif [ "$PROFILE" = cycle ]; then RUN_TIMEOUT=${RUN_TIMEOUT_CYCLE:-2400}
elif [ "$SHORT" = 1 ]; then RUN_TIMEOUT=${RUN_TIMEOUT_SHORT:-3000}
else RUN_TIMEOUT=${RUN_TIMEOUT:-5400}; fi
[[ $RUN_TIMEOUT =~ ^[0-9]+$ ]] || { plog "bad RUN_TIMEOUT '$RUN_TIMEOUT'"; exit 2; }
PB_PLAY_ID=${PB_PLAY_ID:-$(cat "$PB_ROOT/PLAY_ID" 2>/dev/null || true)}
export PB_PLAY_ID

# STATUS.json -------------------------------------------------------------------------------
# One file per results root, rewritten (atomically) at every state change and after every run.
NCONDS=$(wc -w <<<"$CONDS"); NREPS=$(wc -w <<<"$REP_LIST")
TOTAL_RUNS=$((NCONDS * NREPS))
MATRIX_T0=$EPOCHSECONDS
EST_RUN_S=${EST_RUN_S:-}
[ "$SHORT" = 1 ] && EST_RUN_S=${EST_RUN_S_SHORT:-660}
[ "$PROFILE" = cycle ] && EST_RUN_S=${EST_RUN_S_CYCLE:-720}
RUN_SECS=()            # wall time of every run that ended DONE in this invocation
FAILED_RUNS=() CUR_RUN="" CUR_T0="" CUR_UNIT="" STAGE=start
count_done() {
  local n=0 r c
  for r in $REP_LIST; do for c in $CONDS; do pb_run_done "$RESDIR/$LAYOUT$r/$c" "$SHORT" "$PROFILE" && n=$((n + 1)); done; done
  echo "$n"
}
count_units_done() {   # reps / cycles in which every condition is DONE
  local n=0 r c all
  for r in $REP_LIST; do
    all=1
    for c in $CONDS; do pb_run_done "$RESDIR/$LAYOUT$r/$c" "$SHORT" "$PROFILE" || { all=0; break; }; done
    n=$((n + all))
  done
  echo "$n"
}
status_write() {
  local done_n units_done mean_s src left eta now=$EPOCHSECONDS cur_el=0 tmp=$PB_RESULTS/.STATUS.json.$$
  done_n=$(count_done); units_done=$(count_units_done)
  if [ "${#RUN_SECS[@]}" -gt 0 ]; then
    mean_s=$(( ( $(IFS=+; echo "${RUN_SECS[*]}") ) / ${#RUN_SECS[@]} )); src=measured
  elif [ -n "$EST_RUN_S" ]; then mean_s=$EST_RUN_S; src=app.env
  else mean_s=""; src=none; fi
  left=$((TOTAL_RUNS - done_n - ${#FAILED_RUNS[@]}))
  [ "$left" -ge 0 ] || left=0
  eta=null
  if [ -n "$mean_s" ]; then
    [ -n "$CUR_T0" ] && cur_el=$((now - CUR_T0))
    if [ -n "$CUR_RUN" ] && [ "$left" -gt 0 ]; then
      rem=$((mean_s - cur_el)); [ "$rem" -ge 0 ] || rem=0
      eta=$((now + rem + (left - 1) * mean_s))
    else
      eta=$((now + left * mean_s))
    fi
    [ "$STAGE" = finished ] && eta=$now
  fi
  # rep layout: the fields as before plus layout/profile; cycle layout: rep_list is [] and the
  # cycles are in cycle_list, cycles_total, cycles_done (every condition DONE), current_cycle
  jq -n --arg app "$APP" --arg reps "$([ "$LAYOUT" = rep ] && echo "$REP_LIST")" \
    --arg cycles "$([ "$LAYOUT" = cycle ] && echo "$REP_LIST")" --arg layout "$LAYOUT" --arg profile "$PROFILE" \
    --argjson units_done "$units_done" --arg cur_unit "$CUR_UNIT" \
    --arg conds "$CONDS" --argjson total "$TOTAL_RUNS" \
    --argjson 'done' "$done_n" --arg failed "${FAILED_RUNS[*]:-}" --arg cur "$CUR_RUN" \
    --arg cur_t0 "$CUR_T0" --argjson t0 "$MATRIX_T0" --arg mean "${mean_s:-}" --arg src "$src" \
    --argjson eta "$eta" --argjson now "$now" --arg stage "$STAGE" --argjson short "$([ "$SHORT" = 1 ] && echo true || echo false)" \
    --argjson rt "$RUN_TIMEOUT" --arg play "${PB_PLAY_ID:-}" --argjson nmeas "${#RUN_SECS[@]}" \
    '{app:$app, rep_list:($reps|split(" ")|map(select(length>0)|tonumber)), conds:($conds|split(" ")),
      total_runs:$total, done_runs:$done,
      failed_runs:($failed|split(" ")|map(select(length>0))|length),
      failed_run_ids:($failed|split(" ")|map(select(length>0))),
      current_run:(if $cur=="" then null else $cur end),
      current_run_started_at:(if $cur_t0=="" then null else ($cur_t0|tonumber) end),
      matrix_started_at:$t0,
      mean_run_seconds:(if $mean=="" then null else ($mean|tonumber) end),
      mean_run_seconds_source:$src, runs_timed:$nmeas,
      eta_finish_epoch:$eta, last_update_epoch:$now,
      stage:$stage, short:$short, run_timeout_s:$rt, play_id:(if $play=="" then null else $play end),
      layout:$layout, profile:$profile}
     + (if $layout == "cycle" then
          {cycle_list:($cycles|split(" ")|map(select(length>0)|tonumber)),
           cycles_total:($cycles|split(" ")|map(select(length>0))|length), cycles_done:$units_done,
           current_cycle:(if $cur_unit=="" then null else ($cur_unit|tonumber) end)}
        else {} end)' \
    > "$tmp" && mv -f "$tmp" "$PB_RESULTS/STATUS.json"
}

plog "matrix start app=$APP ns=$APP_NS ${LAYOUT}s='$REP_LIST' profile=$PROFILE short=$SHORT conds='$CONDS' retries=$RETRIES run_timeout=${RUN_TIMEOUT}s play=${PB_PLAY_ID:-?}"
STAGE=prepull; status_write

# another benchmark app still deployed?
for env in "$PB_APPS"/*/app.env; do
  other=$(basename "$(dirname "$env")")
  [ "$other" = "$APP" ] && continue
  ons=$(bash -c "set -a; . '$env' >/dev/null 2>&1; echo \"\${APP_NS:-}\"")
  [ -n "$ons" ] && [ "$ons" != "$APP_NS" ] || continue
  if K get ns "$ons" >/dev/null 2>&1; then
    if [ "$FORCE_OTHER" = 1 ]; then plog "WARNING: namespace $ons ($other) exists; continuing (--force-other-apps)"
    else plog "namespace $ons of app $other exists; undeploy it first (apps/$other/undeploy.sh) or pass --force-other-apps"; STAGE=refused; status_write; exit 1; fi
  fi
done

# pre-pull, deploy -----------------------------------------------------------------------
pb_resolve_nodes
if [ -f "$PB_APP_DIR/images.txt" ]; then
  plog "pre-pulling $(grep -cvE '^[[:space:]]*(#|$)' "$PB_APP_DIR/images.txt") images on $PB_NODES"
  pids=()
  for n in $PB_NODES; do
    # shellcheck disable=SC2016  # the loop runs on the node
    grep -vE '^[[:space:]]*(#|$)' "$PB_APP_DIR/images.txt" | awk '{print $1}' | \
      pb_on_in "$n" 'while read -r i; do k3s crictl inspecti "$i" >/dev/null 2>&1 && continue; k3s crictl pull "$i" >/dev/null 2>&1 || echo "pull failed: $i"; done' \
      > "$RESDIR/prepull.$n.log" 2>&1 &
    pids+=("$!")
  done
  wait "${pids[@]}"
  for n in $PB_NODES; do
    [ -s "$RESDIR/prepull.$n.log" ] && plog "WARNING prepull $n: $(tr '\n' ' ' < "$RESDIR/prepull.$n.log" | head -c 400)"
  done
else
  plog "WARNING: no images.txt; first runs may pay image pulls"
fi
plog "deploy $APP"
STAGE=deploy; status_write
t_dep=$EPOCHSECONDS
if ! bash "$PB_APP_DIR/deploy.sh" > "$RESDIR/deploy.log" 2>&1; then
  plog "DEPLOY FAILED: $(tail -n 5 "$RESDIR/deploy.log" | tr '\n' ' ')"
  STAGE=deploy_failed; status_write
  exit 1
fi
plog "deploy ok in $((EPOCHSECONDS - t_dep))s"
STAGE=running; status_write

# runs -------------------------------------------------------------------------------------
for rep in $REP_LIST; do
  U=$LAYOUT$rep        # rep<r> or cycle<k>
  mkdir -p "$RESDIR/$U"
  ofile=$RESDIR/$U/ORDER.json
  seq_i=""
  if [ -f "$ofile" ] && [ "$(jq -r '.conds | sort | join(" ")' "$ofile")" = "$(tr ' ' '\n' <<<"$CONDS" | sort | tr '\n' ' ' | sed 's/ $//')" ]; then
    seed=$(jq -r .seed "$ofile"); order=$(jq -r '.order | join(" ")' "$ofile"); design=$(jq -r '.design // "shuffle"' "$ofile")
    seq_i=$(jq -r '.sequence // empty' "$ofile")
  elif [ "$LAYOUT" = cycle ]; then
    # shellcheck disable=SC2086
    read -r seed design seq_i order <<<"$(pb_williams "$APP" "$rep" $CONDS)"
    if [ "$design" = williams ]; then how='Williams design for 5 treatments (bin/lib.sh pb_williams): 10 sequences from first row 0 1 4 2 3, its cyclic shifts and their mirror images; treatment t = canonical condition t; cycles 10(b-1)+1..10b use the sequences in the order random.Random(int(sha256("<app>:williams:<b>")[:8],16)).shuffle(range(10))'
    elif [ "$design" = permutations ]; then how='all n! orders of the conditions form one block (bin/lib.sh pb_williams), each block shuffled with random.Random(int(sha256("<app>:perm:<block>")[:8],16))'
    else how='random.Random(int(sha256("<app>:cycle<k>")[:8],16)).shuffle(canonical conds)'; fi
    BLOCK_N=10; if [ "$design" = permutations ]; then BLOCK_N=$(( $(wc -w <<<"$CONDS") == 3 ? 6 : 2 )); fi
    jq -n --arg app "$APP" --argjson cycle "$rep" --argjson seed "$seed" --arg design "$design" \
      --arg seq "$seq_i" --arg order "$order" --arg conds "$CONDS" --arg how "$how" \
      --argjson block "$(( (rep - 1) / BLOCK_N + 1 ))" \
      '{app:$app, cycle:$cycle, seed:$seed, design:$design,
        sequence:(if $seq=="-" or $seq=="" then null else ($seq|tonumber) end), block:$block,
        conds:($conds|split(" ")), order:($order|split(" ")), how:$how}' > "$ofile"
  else
    # shellcheck disable=SC2086
    read -r seed design order <<<"$(pb_shuffle "$APP" "$rep" $CONDS)"
    if [ "$design" = balanced ]; then how='balanced 3x5 position design (bin/lib.sh pb_shuffle), rows = reps 1-3; non-baseline conditions assigned to columns by random.Random(int(sha256("<app>")[:8],16)).shuffle'
    else how='random.Random(int(sha256("<app>:rep<r>")[:8],16)).shuffle(canonical conds)'; fi
    # shellcheck disable=SC2086
    jq -n --arg app "$APP" --argjson rep "$rep" --argjson seed "$seed" --arg design "$design" \
      --arg order "$order" --arg conds "$CONDS" --arg how "$how" \
      '{app:$app, rep:$rep, seed:$seed, design:$design, conds:($conds|split(" ")), order:($order|split(" ")), how:$how}' > "$ofile"
  fi
  plog "$U order: $order (seed $seed, $design${seq_i:+ sequence $seq_i})"
  CUR_UNIT=$rep
  pos=0
  for cond in $order; do
    pos=$((pos + 1))
    run=$RESDIR/$U/$cond
    if pb_run_done "$run" "$SHORT" "$PROFILE"; then plog "$U $cond SKIP (DONE)"; continue; fi
    ok_run=0
    for attempt in $(seq 1 $((RETRIES + 1))); do
      plog "$U $cond START (attempt $attempt, position $pos)"
      t0=$EPOCHSECONDS
      CUR_RUN="$U/$cond" CUR_T0=$t0; status_write
      pflag=()
      case $PROFILE in short) pflag=(--short) ;; cycle) pflag=(--profile cycle) ;; esac
      PB_ORDER_SEED=$seed PB_ORDER_POS=$pos PB_ATTEMPT=$attempt PB_ORDER_DESIGN=$design PB_ORDER_SEQ=$seq_i \
        timeout --signal=TERM --kill-after=180 "$RUN_TIMEOUT" bash "$PB_BIN/run_one.sh" "$APP" "$cond" "$rep" "${pflag[@]}" \
        >> "$RESDIR/run_one.out" 2>&1
      rc=$?
      if pb_run_done "$run" "$SHORT" "$PROFILE"; then
        w=$(wc -l < "$run/warnings.txt" 2>/dev/null || echo 0)
        plog "$U $cond OK in $((EPOCHSECONDS - t0))s (warnings: $w)"
        RUN_SECS+=("$((EPOCHSECONDS - t0))"); ok_run=1
        CUR_RUN="" CUR_T0=""; status_write
        break
      fi
      msg=$(head -c 400 "$run/FAILED" 2>/dev/null | tr '\n' ' ')
      [ "$rc" = 124 ] && msg="timeout after ${RUN_TIMEOUT}s; $msg"
      plog "$U $cond FAILED rc=$rc after $((EPOCHSECONDS - t0))s: ${msg:-no FAILED file}"
    done
    if [ "$ok_run" = 0 ]; then FAILED_RUNS+=("$U/$cond"); CUR_RUN="" CUR_T0=""; status_write; fi
  done
  CUR_UNIT=""
done

# summary ------------------------------------------------------------------------------------
ndone=0 nfail=0 missing=""
for rep in $REP_LIST; do
  for cond in $CONDS; do
    if pb_run_done "$RESDIR/$LAYOUT$rep/$cond" "$SHORT" "$PROFILE"; then ndone=$((ndone + 1)); else nfail=$((nfail + 1)); missing+="$LAYOUT$rep/$cond "; fi
  done
done
plog "matrix end: $ndone DONE, $nfail not done${missing:+ ($missing)} in $((EPOCHSECONDS - MATRIX_T0))s"
STAGE=finished; status_write
if [ "$nfail" = 0 ] && [ "$KEEP" = 0 ]; then
  plog "undeploy $APP"
  bash "$PB_APP_DIR/undeploy.sh" > "$RESDIR/undeploy.log" 2>&1 || plog "WARNING: undeploy failed"
elif [ "$nfail" != 0 ]; then
  plog "app left deployed so the missing runs can be resumed: run_matrix.sh $APP --$LAYOUT-list '$REP_LIST'$([ "$SHORT" = 1 ] && echo ' --short')"
fi
[ "$nfail" = 0 ]
