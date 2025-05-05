# Copyright 2025 Cisco Systems, Inc. and its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

# Description: This is an example client demonstrating -
# ACP request for a stateless run using /runs/wait Endpoint
# Prerequisites: create a .env similar to .env.sample based on the Agent deployment output (Refer deploy_acp/README.md).
# Usage: python clients/acp_client/client_rest.py
source .env

echo "API_PORT=$API_PORT"
echo "API_KEY=$API_KEY"
echo "AGENT_ID=$AGENT_ID"

curl -s -H "content-type: application/json" \
     -H "x-api-key: $API_KEY" \
     -d '{
       "agent_id": "'"$AGENT_ID"'",
       "input": {
         "messages": [
           {
              "type": "human",
              "content": "get details for project APT"
          }
         ]
       },
       "config": {
         "configurable": {}
       }
     }' \
     http://127.0.0.1:$API_PORT/runs/wait
