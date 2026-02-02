#!/bin/bash
set -e

OASF_TEMP_DIR="oasf_records"
mkdir -p "$OASF_TEMP_DIR"

cleanup() {
    echo "Cleaning up: stopping oasf-translation-service..."
    docker-compose down oasf-translation-service || true
    echo "Removing temp dir $OASF_TEMP_DIR..."
    rm -rf "$OASF_TEMP_DIR"
    echo "Cleanup completed"
}
trap cleanup EXIT

echo "🚀 Starting agent cards publishing process..."

echo "Setting PYTHONPATH to current directory..."
export PYTHONPATH=$(pwd)
echo "PYTHONPATH set to: $PYTHONPATH"

echo "Starting oasf-translation-service..."
docker-compose up -d oasf-translation-service

echo "Waiting for oasf-translation-service to be ready..."
timeout=60; counter=0
while [ $counter -lt $timeout ]; do
    if docker-compose ps oasf-translation-service | grep -q "Up"; then
        echo "✅ oasf-translation-service is up"
        break
    fi
    echo "Waiting for oasf-translation-service... ($counter/$timeout)"
    sleep 2
    counter=$((counter + 2))
done
if [ $counter -ge $timeout ]; then
    echo "❌ Timeout waiting for oasf-translation-service to start"
    exit 1
fi

echo "Ensuring dir-apiserver and zot containers are up..."
docker-compose up -d dir-api-server dir-mcp-server zot

echo "Waiting for dir-apiserver to be healthy..."
timeout=120; counter=0
while [ $counter -lt $timeout ]; do
    if docker-compose ps dir-api-server | grep -q "Up"; then
        echo "✅ dir-api-server is healthy"
        break
    fi
    echo "Waiting for dir-apiserver to be healthy... ($counter/$timeout)"
    sleep 5
    counter=$((counter + 5))
done
if [ $counter -ge $timeout ]; then
    echo "❌ Timeout waiting for dir-apiserver to be healthy"
    exit 1
fi

echo "⏳ Waiting for zot to be healthy..."
timeout=120; counter=0
while [ $counter -lt $timeout ]; do
    if docker-compose ps zot | grep -q "Up"; then
        echo "✅ zot is healthy"
        break
    fi
    echo "Waiting for zot to be healthy... ($counter/$timeout)"
    sleep 5
    counter=$((counter + 5))
done
if [ $counter -ge $timeout ]; then
    echo "❌ Timeout waiting for zot to be healthy"
    exit 1
fi

echo "Running agent records publishing script with uv..."
if command -v uv &> /dev/null; then
    echo "Using uv to run the script..."
    uv run python scripts/publish_agent_records.py
else
    echo "⚠️  uv not found, falling back to python..."
    python scripts/publish_agent_records.py
fi

echo "Moving agent JSONs to corresponding folders (slugified with hyphens)..."
mkdir -p agents/supervisors/auction/oasf/agents
mkdir -p agents/supervisors/logistics/oasf/agents

slugify() {
    echo "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g' | sed -E 's/^-+|-+$//g'
}

for json in "$OASF_TEMP_DIR"/*.json; do
    fname=$(basename "$json")
    slug=$(slugify "${fname%.json}").json
    case "$fname" in
        Auction_Supervisor_agent.json|Brazil_Coffee_Farm.json|Colombia_Coffee_Farm.json|Vietnam_Coffee_Farm.json)
            mv "$json" "agents/supervisors/auction/oasf/agents/$slug"
            ;;
        Logistics_Supervisor_agent.json|Logistics_Helpdesk.json|Shipping_agent.json|Tatooine_Farm_agent.json|Accountant_agent.json)
            mv "$json" "agents/supervisors/logistics/oasf/agents/$slug"
            ;;
        *)
            echo "Skipping $fname (no matching folder)"
            ;;
    esac
done

echo "Agent cards publishing completed successfully!"
echo "Translation service will be stopped during cleanup..."