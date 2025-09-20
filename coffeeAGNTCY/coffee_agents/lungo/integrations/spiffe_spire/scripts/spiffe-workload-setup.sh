#!/bin/sh
# Exit immediately if any command exits with a non-zero status
# Treat unset variables as an error and exit immediately
set -eu

SPIFFE_SOCKET="${SPIFFE_SOCKET_PATH:-/tmp/spire-agent/private/api.sock}"
SVID_DIR="${SPIFFE_CERTS_DIR:-/var/run/spiffe/workload}"
JWT_PATH="${SPIFFE_JWT_FILE_PATH:-/var/run/spiffe/workload/spiffe-jwt.token}"
JWT_FILE="$(basename "$JWT_PATH")"
AUDIENCE="${AUDIENCE}"

# all times in seconds
JWT_WAIT_TIMEOUT="${JWT_WAIT_TIMEOUT:-120}"        
JWKS_WAIT_TIMEOUT="${JWKS_WAIT_TIMEOUT:-120}"     
JWKS_REFRESH="${JWKS_REFRESH:-300}"

OIDC_BASE="${OIDC_BASE:-http://spire-oidc:8080}"
JWKS_PATH="$SVID_DIR/jwks.json"
WRAPPED_JWKS="$SVID_DIR/key.jwt" 

# prepare directories & config
mkdir -p "$SVID_DIR"
install -d -m 0755 /etc/spiffe

cat > /etc/spiffe/helper.conf <<EOF
agent_address = "$SPIFFE_SOCKET"
cert_dir = "$SVID_DIR"
daemon_mode = true
jwt_svids = [{
  jwt_audience       = "$AUDIENCE"
  jwt_svid_file_name = "$JWT_FILE"
}]
EOF

# start spiffe-helper in background
/usr/bin/spiffe-helper -config /etc/spiffe/helper.conf -daemon-mode=true &
HELPER_PID=$!
echo "Started spiffe-helper (pid $HELPER_PID)"

# ensure background processes are cleaned up if setup fails before exec
cleanup() { kill "$HELPER_PID" "$JWKS_PID" 2>/dev/null || true; }
trap cleanup EXIT

# wait for JWT SVID with timeout
echo "Waiting for JWT SVID at $SVID_DIR/$JWT_FILE…"
elapsed=0
interval=1
while [ $elapsed -lt $JWT_WAIT_TIMEOUT ]; do
  if [ -s "$SVID_DIR/$JWT_FILE" ]; then
    echo "JWT SVID ready"
    break
  fi
  sleep $interval
  elapsed=$((elapsed + interval))
done
[ -s "$SVID_DIR/$JWT_FILE" ] || { echo "ERROR: no JWT after ${JWT_WAIT_TIMEOUT}s"; exit 1; }

# fetch initial JWKS with timeout
echo "Fetching initial JWKS from $OIDC_BASE/keys…"
elapsed=0
interval=1
while [ $elapsed -lt $JWKS_WAIT_TIMEOUT ]; do
  if curl -fsSL "$OIDC_BASE/keys" -o "$JWKS_PATH"; then
    echo "JWKS fetched"
    break
  fi
  sleep $interval
  elapsed=$((elapsed + interval))
done
[ -s "$JWKS_PATH" ] || { echo "ERROR: no JWKS after ${JWKS_WAIT_TIMEOUT}s"; exit 1; }

# wrap JWKS for your verifier (base64, single-line JSON)
B64_JWKS="$(base64 -w0 "$JWKS_PATH")"
printf '{"jwks":"%s"}' "$B64_JWKS" > "$WRAPPED_JWKS"
echo "Initial JWKS written to $WRAPPED_JWKS"

# start JWKS refresher in background
jwks_refresher() {
  while sleep "$JWKS_REFRESH"; do
    tmp="${JWKS_PATH}.new"
    if curl -fsSL "$OIDC_BASE/keys" -o "$tmp"; then
      if ! cmp -s "$JWKS_PATH" "$tmp"; then
        mv "$tmp" "$JWKS_PATH"
        B64_JWKS="$(base64 -w0 "$JWKS_PATH")"
        printf '{"jwks":"%s"}' "$B64_JWKS" > "$WRAPPED_JWKS"
        echo "JWKS refreshed"
      else
        rm -f "$tmp"
      fi
    fi
  done
}
jwks_refresher & JWKS_PID=$!

# Hand off to the CMD from docker compose keeping background helper/refresher alive.
exec "$@"
