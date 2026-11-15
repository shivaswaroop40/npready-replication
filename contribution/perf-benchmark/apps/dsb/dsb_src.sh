#!/usr/bin/env bash
# Put the DeathStarBench fork files that the nginx-thrift and media-frontend init containers copy
# on every worker, once per play, at /var/lib/perfbench/dsb-src/DeathStarBench (read-only hostPath
# in manifest.yaml). The thesis manifest cloned the fork (about 130 MB) from GitHub at every pod
# start; with a restart before every run that was two clones per run. Here cp-01 clones once, at
# the pinned commit, keeps only the six directories the init containers read, and copies them to
# each worker over ssh. Idempotent: a node whose copy already carries the commit and tree hash is
# left alone. Prints one JSON line.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/../common.sh"
pb_init "$HERE" src

SHA=0d49cb4d37aa1fa204bccf1a6d4a6179312ac804
URL=https://github.com/dimoibiehg/DeathStarBench.git
DIR=/var/lib/perfbench/dsb-src/DeathStarBench
PARTS="socialNetwork/gen-lua socialNetwork/docker/openresty-thrift/lua-thrift socialNetwork/nginx-web-server/lua-scripts
socialNetwork/nginx-web-server/pages socialNetwork/keys socialNetwork/media-frontend/lua-scripts"
SSH=(ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=8 -o LogLevel=ERROR)
tree_hash() { (cd "$1" && find . -type f ! -name '.perfbench-*' -print0 | sort -z | xargs -0 sha256sum | sha256sum | cut -c1-64); }

cloned=false
if [ "$(cat "$DIR/.perfbench-commit" 2>/dev/null)" != "$SHA" ] || [ ! -s "$DIR/.perfbench-tree" ] \
   || [ "$(tree_hash "$DIR")" != "$(cat "$DIR/.perfbench-tree")" ]; then
  tmp=$(mktemp -d /var/tmp/dsb-src.XXXXXX)
  trap 'rm -rf "$tmp"' EXIT
  pb_log "cloning $URL at $SHA (once per play)"
  git clone -q "$URL" "$tmp/repo"
  git -C "$tmp/repo" checkout -q "$SHA"
  mkdir -p "$tmp/out"
  # shellcheck disable=SC2086  # PARTS is a word list
  (cd "$tmp/repo" && tar cf - $PARTS) | (cd "$tmp/out" && tar xf -)
  echo "$SHA" > "$tmp/out/.perfbench-commit"
  tree_hash "$tmp/out" > "$tmp/out/.perfbench-tree"
  mkdir -p "$(dirname "$DIR")"
  rm -rf "$DIR.old"; [ -d "$DIR" ] && mv "$DIR" "$DIR.old"
  mv "$tmp/out" "$DIR"; rm -rf "$DIR.old"
  cloned=true
fi
TREE=$(cat "$DIR/.perfbench-tree")
SIZE=$(du -sk "$DIR" | cut -f1)

workers=$(kubectl get nodes -o json | jq -r '.items[] | select((.spec.taints // []) | map(.key) | index("node-role.kubernetes.io/control-plane") | not)
  | .status.addresses[] | select(.type == "InternalIP") | .address')
[ -n "$workers" ] || pb_die "no worker nodes found"
copied=""
for ip in $workers; do
  have=$("${SSH[@]}" "root@$ip" "cat '$DIR/.perfbench-tree' 2>/dev/null" </dev/null || true)
  if [ "$have" != "$TREE" ]; then
    tar -C "$DIR" -cf - . | "${SSH[@]}" "root@$ip" "rm -rf '$DIR.new' && mkdir -p '$DIR.new' && tar -C '$DIR.new' -xf - && rm -rf '$DIR' && mv '$DIR.new' '$DIR'"
    copied+="$ip "
  fi
  got=$("${SSH[@]}" "root@$ip" "cd '$DIR' && find . -type f ! -name '.perfbench-*' -print0 | sort -z | xargs -0 sha256sum | sha256sum | cut -c1-64" </dev/null)
  [ "$got" = "$TREE" ] || pb_die "worker $ip: tree hash $got != $TREE"
done
pb_log "dsb source $SHA (tree $TREE, ${SIZE} KiB) on cp-01 and workers: $(echo $workers); copied to: ${copied:-none}"
jq -cn --arg app "$APP" --arg sha "$SHA" --arg tree "$TREE" --argjson kib "$SIZE" --argjson cloned "$cloned" \
  --arg copied "${copied% }" --argjson secs $(( $(date +%s) - PB_T0 )) \
  '{app: $app, step: "src", ok: true, commit: $sha, tree_sha256: $tree, kib: $kib, cloned: $cloned,
    copied_to: ($copied | split(" ") | map(select(length > 0))), seconds: $secs}'
