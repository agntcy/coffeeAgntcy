#!/bin/bash

# Script to push OASF records to the Directory if they don't already exist
# Usage: ./push_oasf_records.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters for summary
TOTAL_RECORDS=0
ALREADY_EXISTS=0
PUSHED=0
FAILED=0

# Get the script's directory and navigate to the lungo base
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LUNGO_DIR="$(dirname "$SCRIPT_DIR")"

# OASF directories to process
OASF_DIRS=(
    "$LUNGO_DIR/agents/supervisors/auction/oasf/agents"
    "$LUNGO_DIR/agents/supervisors/logistics/oasf/agents"
)

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  OASF Records Push Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Check if dirctl is installed
echo -e "${YELLOW}[1/3] Checking if dirctl is installed...${NC}"

if ! command -v dirctl &> /dev/null; then
    echo -e "${RED}ERROR: dirctl is not installed.${NC}"
    echo ""
    echo "Please install dirctl using one of the following methods:"
    echo ""
    echo "  From Brew Tap:"
    echo "    brew tap agntcy/dir https://github.com/agntcy/dir/"
    echo "    brew install dirctl"
    echo ""
    echo "  From Release Binaries:"
    echo "    curl -L https://github.com/agntcy/dir/releases/latest/download/dirctl-darwin-arm64 -o dirctl"
    echo "    chmod +x dirctl"
    echo "    sudo mv dirctl /usr/local/bin/"
    echo ""
    echo "  From Source:"
    echo "    git clone https://github.com/agntcy/dir"
    echo "    cd dir"
    echo "    task build-dirctl"
    echo ""
    echo "See: https://github.com/agntcy/dir/tree/main/cli"
    exit 1
fi

DIRCTL_VERSION=$(dirctl --version 2>/dev/null || echo "unknown")
echo -e "${GREEN}✓ dirctl is installed (${DIRCTL_VERSION})${NC}"
echo ""

# Step 2: Process OASF records
echo -e "${YELLOW}[2/3] Processing OASF records...${NC}"
echo ""

for OASF_DIR in "${OASF_DIRS[@]}"; do
    if [[ ! -d "$OASF_DIR" ]]; then
        echo -e "${YELLOW}  Warning: Directory not found: $OASF_DIR${NC}"
        continue
    fi

    RELATIVE_DIR="${OASF_DIR#$LUNGO_DIR/}"
    echo -e "${BLUE}Processing directory: ${RELATIVE_DIR}${NC}"
    echo ""

    # Find all JSON files in the directory
    for JSON_FILE in "$OASF_DIR"/*.json; do
        if [[ ! -f "$JSON_FILE" ]]; then
            continue
        fi

        ((TOTAL_RECORDS++))

        FILENAME=$(basename "$JSON_FILE")
        
        # Extract the agent name from the JSON file
        AGENT_NAME=$(jq -r '.name // empty' "$JSON_FILE" 2>/dev/null)
        
        if [[ -z "$AGENT_NAME" ]]; then
            echo -e "  ${YELLOW}⚠ Skipping $FILENAME: Could not extract agent name${NC}"
            ((FAILED++))
            continue
        fi

        echo -e "  Processing: ${FILENAME}"
        echo -e "    Agent name: \"${AGENT_NAME}\""

        # Check if the agent already exists in the directory
        SEARCH_RESULT=$(dirctl search --name "$AGENT_NAME" --output raw 2>/dev/null || echo "")
        
        if [[ -n "$SEARCH_RESULT" ]]; then
            echo -e "    ${GREEN}✓ Already exists in directory (CID: ${SEARCH_RESULT:0:20}...)${NC}"
            ((ALREADY_EXISTS++))
        else
            echo -e "    ${YELLOW}→ Not found in directory, pushing...${NC}"
            
            # Push the JSON file to the directory
            PUSH_RESULT=$(dirctl push "$JSON_FILE" --output raw 2>&1)
            PUSH_EXIT_CODE=$?
            
            if [[ $PUSH_EXIT_CODE -eq 0 && -n "$PUSH_RESULT" ]]; then
                echo -e "    ${GREEN}✓ Successfully pushed (CID: ${PUSH_RESULT:0:20}...)${NC}"
                ((PUSHED++))
            else
                echo -e "    ${RED}✗ Failed to push: ${PUSH_RESULT}${NC}"
                ((FAILED++))
            fi
        fi
        echo ""
    done
done

# Step 3: Summary
echo -e "${YELLOW}[3/3] Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "  Total OASF records found:  ${TOTAL_RECORDS}"
echo -e "  ${GREEN}Already in directory:        ${ALREADY_EXISTS}${NC}"
echo -e "  ${GREEN}Successfully pushed:         ${PUSHED}${NC}"
if [[ $FAILED -gt 0 ]]; then
    echo -e "  ${RED}Failed:                      ${FAILED}${NC}"
else
    echo -e "  Failed:                      ${FAILED}"
fi
echo -e "${BLUE}========================================${NC}"

if [[ $FAILED -gt 0 ]]; then
    echo -e "${YELLOW}Some records failed to process. Check the output above for details.${NC}"
    exit 1
fi

echo -e "${GREEN}Done!${NC}"
exit 0
