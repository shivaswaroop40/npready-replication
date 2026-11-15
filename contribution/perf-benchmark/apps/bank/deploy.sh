#!/usr/bin/env bash
# Deploy Bank of Anthos v0.6.10 into APP_NS from manifest.yaml. Idempotent.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/../common.sh"
pb_init "$HERE" deploy

pb_ensure_ns
# JWT signing key pair. The thesis applied the demo key from extras/jwt/jwt-secret.yaml; this
# bundle does not ship a private key, so it generates an equivalent one (RSA 4096, same PEM
# formats, same Secret keys) once per namespace. See NOTES.md.
if ! kc get secret jwt-key >/dev/null 2>&1; then
  tmp=$(mktemp -d)
  trap 'rm -rf "$tmp"' EXIT
  chmod 700 "$tmp"
  openssl genrsa -traditional -out "$tmp/jwtRS256.key" 4096 2>/dev/null \
    || openssl genrsa -out "$tmp/jwtRS256.key" 4096 2>/dev/null
  openssl rsa -in "$tmp/jwtRS256.key" -pubout -out "$tmp/jwtRS256.key.pub" 2>/dev/null
  kc create secret generic jwt-key --from-file=jwtRS256.key="$tmp/jwtRS256.key" \
    --from-file=jwtRS256.key.pub="$tmp/jwtRS256.key.pub" >/dev/null
  rm -rf "$tmp"
  trap - EXIT
  pb_log "generated Secret jwt-key"
fi
pb_apply "$APP_DIR/manifest.yaml"
pb_apply "$APP_DIR/steady-configmap.yaml"
# Thesis post-apply steps (spec section 5). manifest.yaml already carries both, so these are no-ops.
kc set env deploy/frontend deploy/userservice deploy/contacts deploy/balancereader deploy/ledgerwriter \
  deploy/transactionhistory ENABLE_TRACING=false ENABLE_METRICS=false >/dev/null
kc scale deploy/loadgenerator --replicas=0 >/dev/null
pb_wait_all "$READY_TIMEOUT"
session=$("$APP_DIR/session.sh")
pb_state_json session:="$session"
