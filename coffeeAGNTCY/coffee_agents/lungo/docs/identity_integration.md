# Identity Integration Documentation

## Agntcy Identity SaaS Integration

### Setting Up the Local Development Environment

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
    - **Vietnam Farm Agent URL**: `http://127.0.0.1:9997/.well-known/agent.json` (corresponds to `VIETNAM_FARM_AGENT_URL`).
    - **Colombia Farm Agent URL**: `http://127.0.0.1:9998/.well-known/agent.json` (corresponds to `COLOMBIA_FARM_AGENT_URL`).


## AGNTCY Open Source Identity Integration

### Prerequisites

1. **Install ngrok CLI**  
   Download and install the ngrok CLI from [ngrok's official website](https://ngrok.com/download).

2. **Run the `start_ngrok.sh` Script**  
   This script sets up a public tunnel to your local machine on port `4444`.  
   Execute the script from the `lungo` directory root:
   ```bash
   ./scripts/start_ngrok.sh
   ```
   Note the generated public URL, as it will be needed in later steps.

   **Extra**: To stop ngrok, simply terminate the process (e.g., `Ctrl+C` in the terminal).
   ```bash
   ps aux | grep ngrok # Find the ngrok process ID
   kill -9 <process_id> # Replace <process_id> with the actual ID
   ```
---

### Local Development Setup

Follow these steps to configure your local development environment:

1. **Start Hydra Services**  
   After running the `start_ngrok.sh` script (which updates the issuer URL), start all services using Docker Compose:
   ```bash
   # override the default docker-compose file to include identity oss envs
   docker-compose -f docker-compose.hydra.yaml up
   ```

2. **Run the Identity Node Services**  
   Open a new terminal, clone the Identity repository, and navigate to its root directory:
   ```bash
   git clone https://github.com/agntcy/identity
   cd identity
   ```
   Start the Identity service:
   ```bash
   ./deployments/scripts/identity/launch_node.sh
   ```

3. **Register an Identity Provider**  
   To set up initially, ensure the OSS Identity CLI is installed. Then, navigate to the lungo directory and execute:
   ```bash
4. Open a new terminal, navigate to the `lungo` directory, and run:
   ```bash
   python ./scripts/register_issuer.py
   ```
   **Note:** If the issuer URL changes, you must re-register the Identity Provider.

4. **Run Lungo Agents**  
   You have two options to run the Lungo agents with OSS Identity environment variables:

    - **Option 1: Run via Docker Compose**  
      Use the following command to start the agents:
      ```bash
      # override the default docker-compose file to include identity oss envs
      docker-compose -f docker-compose.yaml -f docker-compose.identity-oss.yaml up
      ```

    - **Option 2: Run Locally**  
      Configure the following environment variables in your shell or a `.env` file:
      ```bash
      IDENTITY_NODE_USE_SSL=0 # Disable SSL verification for local development
      IDENTITY_NODE_GRPC_SERVER_URL=127.0.0.1:4001 # Identity Node gRPC server URL (no http/https prefix)
      ENABLE_OSS_IDENTITY=true # Enable OSS Identity for lungo agents
      IDP_ISSUER_URL=<ngrok-url> # Public URL from step 1
      HYDRA_ADMIN_URL=<your-hydra-admin-url> # Default: http://localhost:4445/clients (if using docker-compose)
      ```
      Then, start the farm servers:
      ```bash
      IDENTITY_NODE_USE_SSL=0 IDENTITY_NODE_GRPC_SERVER_URL=127.0.0.1:4001 ENABLE_OSS_IDENTITY=true IDP_ISSUER_URL=https://c510286bae99.ngrok-free.app ENABLE_HTTP=true uv run python farms/vietnam/farm_server.py # Replace with colombia for Colombia farm
      ```
      For the exchange server:
      ```bash
      IDENTITY_NODE_USE_SSL=0 IDENTITY_NODE_GRPC_SERVER_URL=127.0.0.1:4001 ENABLE_OSS_IDENTITY=true IDP_ISSUER_URL=https://cc5ec0986c38.ngrok-free.app uv run python exchange/main.py
      ```