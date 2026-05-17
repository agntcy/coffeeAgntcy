#!/bin/sh
set -e

SERVER_ADDR="${DIRECTORY_CLIENT_SERVER_ADDRESS:-dir-api-server:8888}"
OASF_DIR="/oasf"
MAX_RETRIES=30
RETRY_INTERVAL=5

echo "Waiting for dir-api-server at ${SERVER_ADDR}..."

retries=0
until dirctl search --server-addr "$SERVER_ADDR" --name "__probe__" --output raw >/dev/null 2>&1; do
  retries=$((retries + 1))
  if [ "$retries" -ge "$MAX_RETRIES" ]; then
    echo "ERROR: dir-api-server not ready after $((MAX_RETRIES * RETRY_INTERVAL))s, giving up."
    exit 1
  fi
  sleep "$RETRY_INTERVAL"
done

echo "dir-api-server is ready."

total=0
pushed=0
skipped=0
failed=0

for f in $(find "$OASF_DIR" -name "*.json" -type f | sort); do
  [ -f "$f" ] || continue
  total=$((total + 1))

  name=$(python3 -c "import json,sys; print(json.load(sys.stdin).get('name',''))" < "$f" 2>/dev/null)
  if [ -z "$name" ]; then
    echo "SKIP: $(basename "$f") (no name field)"
    skipped=$((skipped + 1))
    continue
  fi

  existing=$(dirctl search --server-addr "$SERVER_ADDR" --name "$name" --output raw 2>/dev/null || true)
  if [ -n "$existing" ] && [ "$existing" != "[]" ]; then
    echo "EXISTS: $name"
    skipped=$((skipped + 1))
    continue
  fi

  cid=$(dirctl push "$f" --server-addr "$SERVER_ADDR" --output raw 2>&1) || {
    echo "FAIL push: $name ($cid)"
    failed=$((failed + 1))
    continue
  }

  cid=$(echo "$cid" | tr -d '[:space:]')

  dirctl pull "$cid" --server-addr "$SERVER_ADDR" --output json >/dev/null 2>&1 || true
  dirctl routing publish "$cid" --server-addr "$SERVER_ADDR" --output json >/dev/null 2>&1 || {
    echo "FAIL routing: $name"
    failed=$((failed + 1))
    continue
  }

  echo "PUSHED: $name"
  pushed=$((pushed + 1))
done

echo ""
echo "Done: $total records, $pushed pushed, $skipped skipped, $failed failed."

if [ "$failed" -gt 0 ]; then
  exit 1
fi
