# Corto Exchange, Farm Server, UI

## Overview

The Corto demo demonstrates the integration of an A2A client within a LangGraph workflow with an A2A server agent. It models a simplified agent system that acts as a coffee sommelier.

The Exchange Agent acts as a client interface, receiving prompts from the user interface about coffee flavor profiles and forwarding them to the farm agent.

The Farm Agent serves as a backend flavor profile generator, processing incoming requests and returning descriptive output.

The user interface forwards all prompts to the exchange’s API, which are then given to a LangGraph which contains an A2A client node. This A2A client node connects to the farm’s A2A server. The underlying A2A transport layer is fully configurable. By default, the system uses AGNTCY's SLIM. 


## Running Corto Locally

You can use Corto in two ways:

1. **Local Python**  
   Run each component directly on your machine.

2. **Docker Compose**  
   Quickly spin up all components as containers using Docker Compose.


### Prerequisites

Before you begin, ensure the following tools are installed:

- **uv**: A Python package and environment manager.  
  Install via Homebrew:
  ```sh
  brew install uv
  ```

- **Node.js** version **16.14.0 or higher**  
  Check your version:
  ```sh
  node -v
  ```
  If not installed, download it from the [official Node.js website](https://nodejs.org/).

---
### Setup Instructions

1. **(Optional) Create a Virtual Environment:**
    Initialize your virtual environment using uv:

    ```sh
    uv venv
    source .venv/bin/activate
    ```

2. **Install Dependencies:**
   Run the following command to install all required Python dependencies:

   ```sh
   uv sync
   ```

3. **Configure Environment Variables**  
   Copy the example environment file:
   ```sh
   cp .env.example .env
   ```
   
   **Configure LLM Provider, Credentials and OTEL endpoint**

   Then update `.env` with your LLM provider, credentials and OTEL endpoint. For example:

   *OpenAI:*
   
   ```env
    LLM_PROVIDER=openai
    OPENAI_API_KEY="your_openai_api_key_here"
    OPENAI_ENDPOINT=https://api.openai.com/v1 # Default OpenAI endpoint without proxy
    OPENAI_MODEL_NAME=gpt-4o
   ```

   *Azure OpenAI:*
   
   ```env
    LLM_PROVIDER=azure-openai
    AZURE_OPENAI_ENDPOINT=https://your-azure-resource.openai.azure.com/
    AZURE_OPENAI_DEPLOYMENT=gpt-4-prod
    AZURE_OPENAI_API_KEY=your_azure_api_key
    AZURE_OPENAI_API_VERSION=2023-12-01-preview
   
   ```

   *OTEL:*
   
   ```env
   OTLP_HTTP_ENDPOINT="http://localhost:4318"
   ```
   
  **Optional: Configure Transport Layer**

   You can also set the transport protocol and server endpoint by adding the following optional variables:

   ```env
   DEFAULT_MESSAGE_TRANSPORT=slim
   TRANSPORT_SERVER_ENDPOINT=http://localhost:46357
   ```

   - `DEFAULT_MESSAGE_TRANSPORT`: Defines the message transport protocol used for agent communication.
   - `TRANSPORT_SERVER_ENDPOINT`: The gateway or server endpoint for the specified transport.

   For a list of supported protocols and implementation details, see the [Agntcy App SDK README](https://github.com/agntcy/app-sdk). This SDK provides the underlying interfaces for building communication bridges and agent clients.

  **Optional: Configure Logging Level**
  
	You can configure the logging level using the LOGGING_LEVEL environment variable. During development, it's recommended to use DEBUG for more detailed output. By default, the logging level is set to INFO.
  
  ```env
  	LOGGING_LEVEL=debug
  ```

**Enable Observability with Observe SDK**

Make sure the following Python dependency is installed:
```
ioa-observe-sdk==1.0.18
```

For advanced observability of your multi-agent system, integrate the [Observe SDK](https://github.com/agntcy/observe/blob/main/GETTING-STARTED.md).

- Use the following decorators to instrument your code:
  - `@graph(name="graph_name")`: Captures MAS topology state for observability.
  - `@agent(name="agent_name", description="Some description")`: Tracks individual agent nodes and activities.
  - `@tool(name="tool_name", description="Some description")`: Monitors tool usage and performance.

- **To enable tracing for the Corto multi-agent system:**
  - In code, set the factory with tracing enabled:
    ```python
    AgntcyFactory("corto.exchange", enable_tracing=True)
    ```

- **To start a new trace session for each prompt execution:**  
  Call `session_start()` at the beginning of each prompt execution to ensure each prompt trace is tracked as a new session:
  ```python
  from ioa_observe_sdk import session_start

  # At the start of each prompt execution
  session_start()
  ```

### Execution

>  **Note:** Each service should be started in its **own terminal window** and left running while the app is in use.
>
> **Shortcut:** If you prefer to spin up all services at once without reading through the steps below, you can spin
> up the entire stack via Docker Compose:
> 
>
>```sh
>docker compose up
>```
>
>Once running, access the UI at: [http://localhost:3000/](http://localhost:3000/), access grafana dashboard at: [http://localhost:3001/](http://localhost:3001/)
>
>
> However, it is recommended to go through the steps below to better understand each component's role.

**Step 1: Run the SLIM Message Bus Gateway and Observability stack**

To enable A2A communication over SLIM, you need to run the SLIM message bus gateway. 

Additionally run the observability stack that has OTEL Collector, Grafana and ClickHouse DB.

You can do this by executing the following command:

```sh
docker compose up slim clickhouse-server otel-collector grafana
```

**Step 2: Run the Farm Server**

Start the `farm_server`, which acts as an A2A agent, by executing:

*Local Python Run:*

```sh
uv run python farm/farm_server.py
```

*Docker Compose*

```sh
docker-compose up farm-server --build
```

The `farm_server` listens for requests from the `exchange` and processes them using LangGraph. It generates flavor profiles based on user inputs such as location and season.

**Step 3: Run the Exchange**

Start the `exchange`, which acts as an A2A client, by running:

*Local Python Run:*

```sh
uv run python exchange/main.py
```

*Docker Compose*

```sh
docker-compose up exchange-server --build
```

This starts a FastAPI server that processes user prompts that are sent to a LangGraph supervisor that facilitates worker agent delegation. The A2A client is registered as a worker agent. If a prompt does not match any worker, the supervisor responds politely with a refusal message.

To invoke the exchange, use the /agent/prompt endpoint to send a human-readable prompt to request information about a location's coffee flavor profiles for a specific season. For example:
```bash
curl -X POST http://127.0.0.1:8000/agent/prompt \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What are the flavor notes of Colombian coffee in winter?"
  }'
```

The `exchange` sends user inputs to the `farm_server` and displays the generated flavor profiles. It interacts with the `farm_server` through A2A communication protocols.


**Step 4: Access the UI**

Once the backend and farm server are running, you can access the React UI by starting the frontend development server (from the `exchange/frontend` directory):

*Local Run:*

```sh
npm install
npm run dev
```

*Docker Compose:*

```sh
docker-compose up ui --build
```

By default, the UI will be available at [http://localhost:3000/](http://localhost:3000/).


![Screenshot](images/corto_ui.png)

**Step 5: Visualize OTEL Traces in Grafana**

1. **Access Grafana**  
   Open your browser and go to [http://localhost:3001/](http://localhost:3001/).  
   Log in with the default admin credentials (username: `admin`, password: `admin` unless you changed it).

   ![Screenshot: Grafana Login](images/grafana_login.png)

2. **Connect/Add the ClickHouse Datasource**  
   - In the left sidebar, click on **"Connections" > "Data sources"**.
   - If not already present, add a new **ClickHouse** datasource with the following settings:
     - **Server address:** `clickhouse-server`
     - **Port:** `9000`
     - **Protocol:** `native`
     - **User/Password:** `admin` / `admin`
   - If already present, select the **ClickHouse** datasource (pre-configured in the Docker Compose setup).

   ![Screenshot: ClickHouse Datasource](images/grafana_clickhouse_datasource.png)
   
   ![Screenshot: ClickHouse Connection](images/grafana_clickhouse_connection.png) 

3. **Import the OTEL Traces Dashboard**  
   - In the left sidebar, click on **"Dashboards" > "New" > "Import"**.
   - Upload or paste the JSON definition for the OTEL traces dashboard, located here:  
     [`corto_dashboard.json`](corto_dashboard.json)
   - **When prompted, select `grafana-clickhouse-datasource` as the datasource.**
   - Click **"Import"** to add the dashboard.

   ![Screenshot: Import Dashboard](images/grafana_import_dashboard.png)

4. **View Traces for the Corto Multi-Agent System**  
   - Navigate to the imported dashboard.
   - You should see traces and spans generated by the Corto agents as they process requests.
   - **To view details of a specific trace, click on a TraceID in the dashboard. This will open the full trace and its spans for further inspection.**

   ![Screenshot: OTEL Dashboard](images/dashboard_grafana.png)
   ![Screenshot: OTEL Traces](images/dashboard_traces.png)
