#!/bin/sh
set -eu

apk add --no-cache ca-certificates curl tar >/dev/null

VER="${SPIRE_VERSION:-1.12.4}"
FILE="spire-${VER}-linux-amd64-musl.tar.gz"
URL="https://github.com/spiffe/spire/releases/download/v${VER}/${FILE}"

echo "Downloading SPIRE ${VER}..."
curl -fsSL -o "/tmp/${FILE}" "${URL}"

mkdir -p /opt/spire/bin
tar -xzf "/tmp/${FILE}" -C /tmp
mv "/tmp/spire-${VER}/bin/spire-agent" /opt/spire/bin/spire-agent
chmod +x /opt/spire/bin/spire-agent

# Wait for the join token and server bundle to be created by the spire-server-init script
while [ ! -s /tmp/join-token/agent_join_token.txt ] || [ ! -s /tmp/join-token/server_bundle.pem ]; do
  sleep 1
done

# Read the join token, stripping any newlines. Verify it's not empty.
JOIN_TOKEN="$(tr -d '\r\n' < /tmp/join-token/agent_join_token.txt || true)"
if [ -z "${JOIN_TOKEN}" ]; then
  echo "ERROR: join token file exists but is empty"
  exit 1
fi

echo "Found join token and server bundle, starting agent with token."

echo "Starting SPIRE Agent..."
exec /opt/spire/bin/spire-agent run \
  -config /opt/spire/conf/agent/agent.conf \
  -joinToken "${JOIN_TOKEN}" \
  -trustBundle /tmp/join-token/server_bundle.pem
