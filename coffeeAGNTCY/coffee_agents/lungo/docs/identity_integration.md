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
   This script creates a public tunnel to your local machine on port `4444`.  
   Run the script from the root of the `lungo` directory:
   ```bash
   ./scripts/start_ngrok.sh
   ```
   Copy the generated public URL, as it will be required in later steps.

   **Tip**: To stop ngrok, terminate the process by pressing `Ctrl+C` in the terminal or using the following commands:
   ```bash
   ps aux | grep ngrok # Find the ngrok process ID
   kill -9 <process_id> # Replace <process_id> with the actual ID
   ```

3. **Install OSS Identity CLI**  
   Follow the installation steps in the [OSS Identity CLI Documentation](https://github.com/agntcy/identity?tab=readme-ov-file#step-1-install-the-issuer-cli).

4. **Ensure Python is Installed**  
   Make sure Python (version 3.8 or higher) is installed on your system.

---

### Running Lungo Agents with OSS Identity Local Setup

Follow these steps to set up your local development environment:

1. **Start Hydra and Identity Services**  
   After running the `start_ngrok.sh` script (which updates the issuer URL), start all services using Docker Compose:
   ```bash
   docker-compose -f docker-compose.hydra.yaml up
   ```

2. **Register an Identity Provider**  
   Ensure the OSS Identity CLI is installed. Then, navigate to the `lungo` directory and run:
   ```bash
   python ./scripts/register_issuer.py
   ```
   **Note**: If the issuer URL changes, you must re-register the Identity Provider.

   When registration is successful, you should see the following output:
   ```
   Issuer registration completed.
   ```

3. **Run Lungo Agents**  
   You can run the Lungo agents with OSS Identity environment variables using one of the following methods:

    - **Option 1: Run with Docker Compose**  
      From the root of the `lungo` directory, use the following command to start the agents:
      ```bash
      docker-compose -f docker-compose.yaml -f docker-compose.identity-oss.yaml up
      ```

    - **Option 2: Run Locally**  
      Set the following environment variables in your shell or a `.env` file:
      ```bash
      IDENTITY_NODE_USE_SSL=0 # Disable SSL verification for local development
      IDENTITY_NODE_GRPC_SERVER_URL=127.0.0.1:4001 # Identity Node gRPC server URL (no http/https prefix)
      ENABLE_OSS_IDENTITY=true # Enable OSS Identity for lungo agents
      IDP_ISSUER_URL=<ngrok-url> # Public URL from step 1
      HYDRA_ADMIN_URL=<your-hydra-admin-url> # Default: http://localhost:4445/clients (if using docker-compose)
      ```
      Start the farm servers:
      ```bash
      ENABLE_OSS_IDENTITY=true IDP_ISSUER_URL=https://c510286bae99.ngrok-free.app ENABLE_HTTP=true uv run python farms/vietnam/farm_server.py # Replace with colombia for Colombia farm
      ```
      Start the exchange server:
      ```bash
      ENABLE_OSS_IDENTITY=true IDENTITY_NODE_USE_SSL=0 IDENTITY_NODE_GRPC_SERVER_URL=127.0.0.1:4001 uv run python exchange/main.py
      ```

4. **Testing the Changes**

   You can test the changes by sending requests to the exchange server. Use the following `curl` commands:

    - **Create an order from the Colombia farm (verified identity):**
      ```bash
      curl -X POST http://127.0.0.1:8000/agent/prompt \
        -H "Content-Type: application/json" \
        -d '{
          "prompt": "I want to order coffee from the Columbia farm. I am willing to offer $3.50 per pound for 500 lbs of coffee from the Columbia farm."
        }'
      ```

    - **Create an order from the Brazil farm (unverified identity):**
      ```bash
      curl -X POST http://127.0.0.1:8000/agent/prompt \
        -H "Content-Type: application/json" \
        -d '{
          "prompt": "I want to order coffee from the Brazil farm. I am willing to offer $3.50 per pound for 500 lbs of coffee from the Brazil farm."
        }'
      ```