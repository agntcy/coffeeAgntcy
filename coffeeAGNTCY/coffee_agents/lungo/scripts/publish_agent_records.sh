#!/bin/bash

set -e  # Exit on any error

# Cleanup function to stop the translation service
cleanup() {
    echo "🧹 Cleaning up: stopping oasf-translation-service..."
    docker-compose stop oasf-translation-service || true
    echo "✅ Cleanup completed"
}

# Set up trap to ensure cleanup runs on script exit
trap cleanup EXIT

echo "🚀 Starting agent cards publishing process..."

# 1. Set Python path
echo "📂 Setting PYTHONPATH to current directory..."
export PYTHONPATH=$(pwd)
echo "PYTHONPATH set to: $PYTHONPATH"

# 2. Run docker service: docker-compose up oasf-translation-service
echo "🔧 Starting oasf-translation-service..."
docker-compose up -d oasf-translation-service

# Wait for oasf-translation-service to be ready
echo "⏳ Waiting for oasf-translation-service to be ready..."
timeout=60
counter=0
while [ $counter -lt $timeout ]; do
    if docker-compose ps oasf-translation-service | grep -q "Up"; then
        echo "✅ oasf-translation-service is up"
        break
    fi
    echo "⏳ Waiting for oasf-translation-service... ($counter/$timeout)"
    sleep 2
    counter=$((counter + 2))
done

if [ $counter -ge $timeout ]; then
    echo "❌ Timeout waiting for oasf-translation-service to start"
    exit 1
fi

# 3. Ensure containers dir-apiserver and zot are up
echo "🔍 Ensuring dir-apiserver and zot containers are up..."

# Start dir-apiserver and zot if not already running
docker-compose up -d dirapiserver zot

# Wait for containers to be healthy
echo "⏳ Waiting for dir-apiserver to be healthy..."
timeout=120
counter=0
while [ $counter -lt $timeout ]; do
    if docker-compose ps dirapiserver | grep -q "Up"; then
        echo "✅ dir-apiserver is healthy"
        break
    fi
    echo "⏳ Waiting for dir-apiserver to be healthy... ($counter/$timeout)"
    sleep 5
    counter=$((counter + 5))
done

if [ $counter -ge $timeout ]; then
    echo "❌ Timeout waiting for dir-apiserver to be healthy"
    exit 1
fi

echo "⏳ Waiting for zot to be healthy..."
timeout=120
counter=0
while [ $counter -lt $timeout ]; do
    if docker-compose ps zot | grep -q "Up"; then
        echo "✅ zot is healthy"
        break
    fi
    echo "⏳ Waiting for zot to be healthy... ($counter/$timeout)"
    sleep 5
    counter=$((counter + 5))
done

if [ $counter -ge $timeout ]; then
    echo "❌ Timeout waiting for zot to be healthy"
    exit 1
fi

# 4. Run python publish script with uv
echo "🐍 Running agent records publishing script with uv..."
if command -v uv &> /dev/null; then
    echo "Using uv to run the script..."
    uv run python scripts/publish_agent_records.py
else
    echo "⚠️  uv not found, falling back to python..."
    python scripts/publish_agent_records.py
fi

echo "🎉 Agent cards publishing completed successfully!"
echo "🧹 Translation service will be stopped during cleanup..."