#!/bin/sh
# Exit immediately if any command exits with a non-zero status
# Treat unset variables as an error and exit immediately
set -eu

# Packages we need
# - curl, tar: download/extract
# - file: sanity-check archive type
# - bind-tools, iputils-ping: troubleshooting
# - netcat-openbsd: reliable `nc -z` support
apk add --no-cache curl tar file bind-tools iputils-ping netcat-openbsd ca-certificates >/dev/null

# Fetch & install spire-server CLI (only the CLI binary is needed here)
VER="${SPIRE_CLI_VERSION:-1.12.4}"
FILENAME="spire-${VER}-linux-amd64-musl.tar.gz"
URL="https://github.com/spiffe/spire/releases/download/v${VER}/${FILENAME}"

echo "Downloading SPIRE CLI ${VER} from ${URL}"
curl -fL -o "/tmp/${FILENAME}" "${URL}"

tar -xzf "/tmp/${FILENAME}" -C /tmp
install -m 0755 "/tmp/spire-${VER}/bin/spire-server" /usr/local/bin/spire-server
rm -rf "/tmp/spire-${VER}" "/tmp/${FILENAME}"
echo "SPIRE CLI installed."

# Wait for spire-server gRPC health port (8081) to be reachable
HOST="${SERVER_HOST:-spire-server}"
PORT="${SERVER_PORT:-8081}"

echo "Waiting for ${HOST}:${PORT} to accept TCP…"
TIMEOUT=60
INTERVAL=2
ELAPSED=0
# Try both nc and a lightweight curl attempt; proceed when either works
until (nc -z "${HOST}" "${PORT}" 2>/dev/null) || (curl -m2 -s "${HOST}:${PORT}" >/dev/null 2>&1); do
  if [ "${ELAPSED}" -ge "${TIMEOUT}" ]; then
    echo "ERROR: ${HOST}:${PORT} did not become ready within ${TIMEOUT} seconds."
    exit 1
  fi
  sleep "${INTERVAL}"
  ELAPSED=$((ELAPSED + INTERVAL))
done
echo "${HOST}:${PORT} is reachable."

# Fetch server bundle into the shared volume for the SPIRE Agent
/usr/local/bin/spire-server bundle show > /tmp/join-token/server_bundle.pem
echo "Wrote server bundle to /tmp/join-token/server_bundle.pem"

# Generate a join token (10 minutes TTL) for the SPIRE Agent
/usr/local/bin/spire-server token generate \
  -spiffeID spiffe://example.org/host \
  -ttl 600 > /tmp/token.out

# Extract the token whether output is "Token: <uuid>" or just "<uuid>"
TOKEN="$(awk '/^Token:/{print $2} !/^Token:/{print $1; exit}' /tmp/token.out)"
[ -n "${TOKEN}" ] || { echo "No token parsed from token generate output:"; cat /tmp/token.out; exit 1; }
printf '%s\n' "${TOKEN}" > /tmp/join-token/agent_join_token.txt
echo "Wrote join token to /tmp/join-token/agent_join_token.txt"

# Create workload entries (all parented to the SPIRE Agent)
create_entry () {
  local id="$1"
  /usr/local/bin/spire-server entry create \
    -spiffeID "spiffe://example.org/workload/${id}" \
    -parentID "spiffe://example.org/host" \
    -selector "unix:user:root"
}

create_entry "brazil-farm"
create_entry "colombia-farm"
create_entry "vietnam-farm"
create_entry "exchange-server"
create_entry "weather-mcp-server"

echo "SPIFFE entries created successfully!"
