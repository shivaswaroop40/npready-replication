#!/usr/bin/env bash
# Log in as the Bank of Anthos demo user and store the session cookie value in
# Secret perfbench-session (key "token"), which throughput.yaml reads. The demo login comes
# from the app's own ConfigMap demo-data-config at run time; nothing is stored in this bundle.
# The token never reaches argv or stdout. Prints one JSON line with the token expiry.
# Called by deploy.sh and restart.sh; it is also TP_PRE_HOOK (tokens last 3600 s).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/../common.sh"
pb_init "$HERE" session

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
chmod 700 "$tmp"
kc get cm demo-data-config -o jsonpath='{.data.DEMO_LOGIN_USERNAME}' > "$tmp/user"
kc get cm demo-data-config -o jsonpath='{.data.DEMO_LOGIN_PASSWORD}' > "$tmp/pass"
[ -s "$tmp/user" ] && [ -s "$tmp/pass" ] || pb_die "ConfigMap demo-data-config has no demo login"

home=$(pb_cluster_url "$TP_URL") || pb_die "no frontend Service"
login=${home%/home}/login
code=$(curl -s -o /dev/null -D "$tmp/headers" -w '%{http_code}' --max-time 30 \
  --data-urlencode "username@$tmp/user" --data-urlencode "password@$tmp/pass" "$login" || true)
tr -d '\r' < "$tmp/headers" | sed -n 's/^[Ss]et-[Cc]ookie: token=\([^;]*\).*/\1/p' | head -n 1 | tr -d '\n' > "$tmp/token"
[ -s "$tmp/token" ] || pb_die "POST /login answered $code without a token cookie"

kc create secret generic perfbench-session --from-file=token="$tmp/token" --dry-run=client -o yaml \
  | kc apply -f - >/dev/null
printf 'Cookie: token=%s\n' "$(cat "$tmp/token")" > "$tmp/cookie"
pb_wait_http_ok "$TP_URL" 60 -H @"$tmp/cookie"
exp=$(python3 -c 'import base64,json,sys; p=open(sys.argv[1]).read().split(".")[1]; p+="="*(-len(p)%4); print(json.loads(base64.urlsafe_b64decode(p))["exp"])' "$tmp/token")
printf '{"app":"%s","step":"session","ok":true,"secret":"perfbench-session","login_status":"%s","token_exp_epoch":%s,"seconds":%d}\n' \
  "$APP" "$code" "$exp" $(( $(date +%s) - PB_T0 ))
