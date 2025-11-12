# Identity Integration Documentation

## Setting Up the Local Development Environment

Refer to the [Identity SaaS Documentation](https://identity-docs.outshift.com/docs/intro) for comprehensive details about Identity SaaS and its features.

---

### Setup Identity Provider and Service Applications

1. **Request Access to Identity SaaS**
  - Reach out to the **AGNTCY Identity Team** to gain access to Identity SaaS.
  - Use the Identity SaaS UI to generate API keys for your agents (e.g., Vietnam and Colombia).

2. **Register an Identity Provider**
  - Follow the steps in the [Identity Provider Registration Guide](https://identity-docs.outshift.com/docs/idp) to complete the registration process.

3. **Create Service Applications**
  - Refer to the [Service Application Creation Guide](https://identity-docs.outshift.com/docs/agentic-service) to set up the service applications.
  - Create two service applications with names matching the farm agent cards:
    - **Vietnam Farm Agent Service App**: Name it "Vietnam Coffee Farm".
    - **Colombia Farm Agent Service App**: Name it "Colombia Coffee Farm".

---

### Configuration for Local Development

1. **Set Up Environment Variables**
  - Update the `config.yaml` file in the `coffeeAGNTCY/coffee_agents/lungo` directory or define the following environment variables in your shell:
    - `IDENTITY_VIETNAM_AGENT_SERVICE_API_KEY`: API key for the Vietnam farm agent.
    - `IDENTITY_COLOMBIA_AGENT_SERVICE_API_KEY`: API key for the Colombia farm agent.
    - `IDENTITY_API_KEY`: General Identity SaaS API key.
    - `IDENTITY_API_SERVER_URL`: Identity API endpoint.
    - `VIETNAM_FARM_AGENT_URL` and `COLOMBIA_FARM_AGENT_URL`: URLs for the farm agents' well-known agent cards (provided in Step 6).
  - Alternatively, you can set these environment variables directly in your shell or use a `.env` file.

2. **Retrieve the General Identity API Key**
  - In the SaaS UI, go to the **Settings** option located in the left-hand sidebar.
  - Under the **API Keys** tab, find and copy the general **Identity SaaS API Key**.
  - This corresponds to the `IDENTITY_API_KEY` environment variable and is required for authenticating API requests.

3. **Retrieve Agent Service API Keys**
  - Go to the **Agentic Services** tab in the Identity SaaS UI.
  - Retrieve the following API keys:
    - **Vietnam Agent Service API Key**: Linked to the Vietnam farm agent service app. This corresponds to the `IDENTITY_VIETNAM_AGENT_SERVICE_API_KEY` environment variable.
    - **Colombia Agent Service API Key**: Linked to the Colombia farm agent service app. This corresponds to the `IDENTITY_COLOMBIA_AGENT_SERVICE_API_KEY` environment variable.

4. **Obtain the Identity API Endpoint**
  - Refer to the [Identity API Documentation](https://identity-docs.outshift.com/docs/api) to locate the Identity API endpoint URL.
  - This corresponds to the `IDENTITY_API_SERVER_URL` environment variable and is used for all API requests to Identity SaaS.

5. **Farm Agent URLs**
  - Use the following well-known agent card URLs for local development:
    - **Vietnam Farm Agent URL**: `http://127.0.0.1:9997/.well-known/agent-card.json` (corresponds to `VIETNAM_FARM_AGENT_URL`).
    - **Colombia Farm Agent URL**: `http://127.0.0.1:9998/.well-known/agent-card.json` (corresponds to `COLOMBIA_FARM_AGENT_URL`).


---


### Identity Auth (TBAC) - Local Run

Enable TBAC when running services directly (make targets or `uv run`). Each service gets its own API key via an inline env var or export in its terminal.

Steps:
1. Copy `'.env.example'` to `'.env'`.
2. Ensure `IDENTITY_AUTH_ENABLED="true"` is set (either in `'.env'` or inline).
3. Start each service with its own `IDENTITY_SERVICE_API_KEY`.

Example (Payment MCP service):
```sh
IDENTITY_AUTH_ENABLED="true" IDENTITY_SERVICE_API_KEY=':1+6W2;y4p<)5yKASKPw9uM+!h6p(1d>c472,nJ46c@5:[Ju->carfIO7E+GVQC9' make payment-mcp
```

Example (other services):
```sh
IDENTITY_AUTH_ENABLED="true" IDENTITY_SERVICE_API_KEY='supervisor_key' make auction-supervisor
IDENTITY_AUTH_ENABLED="true" IDENTITY_SERVICE_API_KEY='brazil_key' make brazil-farm
IDENTITY_AUTH_ENABLED="true" IDENTITY_SERVICE_API_KEY='colombia_key' make colombia-farm
IDENTITY_AUTH_ENABLED="true" IDENTITY_SERVICE_API_KEY='vietnam_key' make vietnam-farm
```

---

### Identity Auth (TBAC) - Docker Compose

Compose uses per-service API key variables. Set them in `'.env'` (loaded by `docker-compose.yml`).

Example `'.env'` additions:
```env
IDENTITY_AUTH_ENABLED="true"
IDENTITY_SERVICE_API_KEY_AUCTION_SUPERVISOR=supervisor_key
IDENTITY_SERVICE_API_KEY_PAYMENT_MCP=payment_mcp_key
IDENTITY_SERVICE_API_KEY_BRAZIL_FARM=brazil_key
IDENTITY_SERVICE_API_KEY_COLOMBIA_FARM=colombia_key
IDENTITY_SERVICE_API_KEY_VIETNAM_FARM=vietnam_key
```

Bring up stack:
```sh
docker compose up exchange-server payment-mcp-server brazil-farm-server colombia-farm-server vietnam-farm-server weather-mcp-server
```

If not using `'.env'`, set inline:
```sh
IDENTITY_SERVICE_API_KEY_AUCTION_SUPERVISOR=new_supervisor_key docker compose up exchange-server
```

Production note:
- Each service should read a unified `IDENTITY_SERVICE_API_KEY` inside its container environment rather than multiple per-service variables.
