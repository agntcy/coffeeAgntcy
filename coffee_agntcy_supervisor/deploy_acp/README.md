## Deploying and building an ACP compliant agent

This guide provides details for:
- Deploying an ACP compliant agent via workflow server manager. 
- Building/Modifying an agent to be ACP compliant, so it can be deployed and used via workflow server manager.

### Deploy an agent that is ACP compliant

1. Install Workflow Server manager (if not already installed on your system)

https://docs.agntcy.org/pages/agws/workflow_server_manager.html#getting-started


2. Deploy the Agent using workflow Server Manager
Execute the following command to deploy the agent. The command will create a docker container with the workflow server and the embedded agent code and expose the ACP endpoints.
```bash
wfsm deploy --manifestPath deploy_acp/acorda_agent.json --envFilePath deploy_acp/acorda_agent_env.yaml 
```
The below is an example of the output from the command above.
```
 ✔ Container orgagntcyacorda-org.agntcy.acorda-1  Started                                                                                                                                                      0.2s 
2025-05-02T16:52:18-07:00 INF ---------------------------------------------------------------------
2025-05-02T16:52:18-07:00 INF ACP agent deployment name: org.agntcy.acorda
2025-05-02T16:52:18-07:00 INF ACP agent running in container: org.agntcy.acorda, listening for ACP requests on: http://127.0.0.1:64212
2025-05-02T16:52:18-07:00 INF Agent ID: 47bae4b9-79f7-4158-a694-2a7f47713ddd
2025-05-02T16:52:18-07:00 INF API Key: d6bc7df9-6676-486d-b3b3-60f9d2eeef7f
2025-05-02T16:52:18-07:00 INF API Docs: http://127.0.0.1:64212/agents/47bae4b9-79f7-4158-a694-2a7f47713ddd/docs
2025-05-02T16:52:18-07:00 INF ---------------------------------------------------------------------
...
org.agntcy.acorda-1  | 2025-05-02T16:52:22.600662000-07:00INFO:     Started server process [7]
org.agntcy.acorda-1  | 2025-05-02T16:52:22.600742000-07:00INFO:     Waiting for application startup.
org.agntcy.acorda-1  | 2025-05-02T16:52:22.601615000-07:00INFO:     Application startup complete.
org.agntcy.acorda-1  | 2025-05-02T16:52:22.601704000-07:00INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```
- Save the details above.They are required to populate the clients/.env file. (The details are also saved to a docker-compose file created on your local setup as indicated in the logs above).
- [Server APIs] (http://127.0.0.1:54316/agents/0ea38b60-12b7-41ea-88ed-f2e907a6411c/docs).
- '54316' is API_PORT value to be used by clients accessing the agents endpoints via ACP and workflow server.

3Send a request to the Agent
- ACP request can be sent directly to the server via 'Server API' link provided in step 3 above.
- ACP requests can be sent via clients similar to acorda/clients/acp_client 

### Create an Agent that is ACP compliant and can be deployed via Workflow Server Manager

Ref: https://github.com/agntcy/acp-sdk/tree/main/examples/echo-agent)

1. Create manifest for the agent similar to [this manifest](https://github.com/agntcy/acp-sdk/blob/main/examples/echo-agent/deploy/echo-agent.json)
- Update the langgraph entry point per your code, as part of the deployment options in the manifest.
```bash
  "deployment": {
    "deployment_options": [
      {
        "type": "source_code",
        "name": "source_code_local",
        "url": ".",
        "framework_config": {
          "framework_type": "langgraph",
          "graph": "echo_agent.langgraph:AGENT_GRAPH"
        }
      }
```
- Update the env variables in the manifest, based on the env variables required by your agent.
- Ensure the manifest file is using these [models](https://github.com/agntcy/acp-sdk/blob/main/examples/echo-agent/echo_agent/state.py)
2. Create an env file for the agent based on [this env file](https://github.com/agntcy/acp-sdk/blob/main/examples/echo-agent/deploy/echo_agent_example.yaml)
3. Agent code must follow the directory structure similar to the above example.
4. Use poetry setup with pyproject.toml and install the agent module (poetry install).
