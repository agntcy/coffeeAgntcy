# Identity Integration Documentation

## Local Development Environment Setup

Refer to the [Identity SaaS Documentation](https://identity-docs.staging.outshift.ai/docs/intro) for detailed information about Identity SaaS and its features.

---

### Step 1: Access Identity SaaS
- Contact the **AGNTCY Identity Team** to request access to Identity SaaS.
- Use the Identity SaaS UI to generate API keys for your agents (e.g., Vietnam and Colombia).

### Step 2: Register an Issuer
- Follow the instructions in the [Register an Issuer Guide](https://identity-docs.staging.outshift.ai/docs/idp) to complete the issuer registration process.

### Step 3: Create Service Apps
- Follow the [Create Identity Service Apps Guide](https://identity-docs.staging.outshift.ai/docs/agentic-service) to set up the service apps.
- Create two service apps with names matching the farm agent cards:
   - **Vietnam Farm Agent Service App**: Name the service app "Vietnam Coffee Farm".
   - **Colombia Farm Agent Service App**: Name the service app "Colombia Coffee Farm".
- Once the service apps are created, retrieve the following API keys and configuration details from the **Agentic Services** tab:
   - **Vietnam Agent Service API Key**: Corresponding to the Vietnam farm agent.
   - **Colombia Agent Service API Key**: Corresponding to the Colombia farm agent.

### Step 4: Retrieve General Identity API Key
- Navigate to the **Settings** section in the left sidebar.
- Under the **API Keys** tab, retrieve the general **Identity SaaS API Key**.

### Step 5: Get the Identity API Endpoint
- Refer to the [Identity API Documentation](https://identity-docs.staging.outshift.ai/docs/api) to obtain the Identity API endpoint URL.

### Step 6: Farm Agent URLs
- Use the following well-known agent card URLs for local development:
   - **Vietnam Farm Agent URL**: `http://127.0.0.1:9997/.well-known/agent.json`
   - **Colombia Farm Agent URL**: `http://127.0.0.1:9998/.well-known/agent.json`

### Step 7: Configure Environment Variables
- Update the `config.yaml` file in the `coffeeAGNTCY/coffee_agents/lungo` directory with the following environment variables:
   - `IDENTITY_VIETNAM_AGENT_SERVICE_API_KEY`: API key for the Vietnam farm agent.
   - `IDENTITY_COLOMBIA_AGENT_SERVICE_API_KEY`: API key for the Colombia farm agent.
   - `IDENTITY_API_KEY`: General Identity SaaS API key.
   - `IDENTITY_API_SERVER_URL`: Identity API endpoint.
   - `VIETNAM_FARM_AGENT_URL` and `COLOMBIA_FARM_AGENT_URL`: URLs for the farm agents' well-known agent cards.
- Alternatively, set these variables in your shell environment when running the agents.
