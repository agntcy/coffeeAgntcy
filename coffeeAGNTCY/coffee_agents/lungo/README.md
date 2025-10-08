<!-- TOC -->
  * [Lungo Demo Overview](#lungo-demo-overview)
    * [Overview](#overview)
  * [Running Lungo Locally](#running-lungo-locally)
    * [Prerequisites](#prerequisites)
    * [Setup Instructions](#setup-instructions)
    * [Execution](#execution)
    * [Group Conversation Implementation](#group-conversation-implementation)
    * [Observability](#observability)
      * [Trace Visualization via Grafana](#trace-visualization-via-grafana)
      * [Metrics Computation with AGNTCY's Metrics Computation Engine (MCE)](#metrics-computation-with-agntcys-metrics-computation-engine-mce)
<!-- TOC -->

## Lungo Demo Overview

The **Lungo Demo** is a continuously evolving showcase of interoperable open-source agentic components. Its primary goal is to demonstrate how different components—from the **Agntcy** project and other open-source ecosystems—can work together seamlessly.

### Overview

The current demo models a **supervisor-worker agent ecosystem**, where:

- The **Supervisor Agent** acts as a _Coffee Exchange_, responsible for managing inventory and fulfilling orders.
- The **Worker Agents** represent _Coffee Farms_, which supply the inventory and provide order information.

All agents are implemented as **directed LangGraphs** with **Agent-to-Agent (A2A)** integration. The user interface communicates with the Supervisor’s API to submit prompts. These prompts are processed through the LangGraph and routed via an A2A client to the appropriate Farm’s A2A server.

The underlying A2A transport is configurable. By default, it uses **SLIM**, supporting both broadcast and unicast messaging depending on the context and data requirements.

One notable component is the **Colombia Farm**, which functions as an **MCP client**. It communicates with an MCP server (over SLIM) to retrieve real-time weather data used to calculate coffee yield.

## Running Lungo Locally

You can use Lungo in two ways:

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

1. **(Optional) Create a Virtual Environment**  
   Initialize your virtual environment using `uv`:

   ```sh
   uv venv
   source .venv/bin/activate
   ```

2. **Install Python Dependencies**  
   Use `uv` to install all required dependencies:

   ```sh
   uv sync
   ```

   Navigate to the Lungo project directory, set the PYTHONPATH environment variable to the root directory of the lungo project. This is necessary for running the application locally.

   ```sh
   # In the lungo root directory
   export PYTHONPATH=$(pwd)
   ```

3. **Configure Environment Variables**  
    Copy the example environment file:

   ```sh
   cp .env.example .env
   ```

   **Configure LLM Provider, Credentials and OTEL endpoint**

   Then update `.env` with your LLM provider, credentials and OTEL endpoint. For example:

   _OpenAI:_

   ```env
    LLM_PROVIDER=openai
    OPENAI_API_KEY="your_openai_api_key_here"
    OPENAI_ENDPOINT=https://api.openai.com/v1 # Default OpenAI endpoint without proxy
    OPENAI_MODEL_NAME=gpt-4o
   ```

   _Azure OpenAI:_

   ```env
    LLM_PROVIDER=azure-openai
    AZURE_OPENAI_ENDPOINT=https://your-azure-resource.openai.azure.com/
    AZURE_OPENAI_DEPLOYMENT=gpt-4-prod
    AZURE_OPENAI_API_KEY=your_azure_api_key
    AZURE_OPENAI_API_VERSION=2023-12-01-preview
   ```

   _OTEL:_

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

- **To enable tracing for the Lungo multi-agent system:**

  - In code, set the factory with tracing enabled:
    ```python
    AgntcyFactory("lungo.exchange", enable_tracing=True)
    ```

- **To start a new trace session for each prompt execution:**  
  Call `session_start()` at the beginning of each prompt execution to ensure each prompt trace is tracked as a new session:

  ```python
  from ioa_observe_sdk import session_start

  # At the start of each prompt execution
  session_start()
  ```

---

### Execution

> **Note:** Each service should be started in its **own terminal window** and left running while the app is in use.
>
> **Shortcut:** If you prefer to spin up all services at once without reading through the steps below, you canspin
> up the entire stack via Docker Compose:
>
> ```sh
> docker compose up
> ```
>
> Once running, access the UI at: [http://localhost:3000/](http://localhost:3000/), access grafana dashboard at: [http://localhost:3001/](http://localhost:3001/)
>
> However, it is recommended to go through the steps below to better understand each component's role.

**Step 1: Run the SLIM Message Bus Gateway and Observability stack**

To enable A2A communication over SLIM, you need to run the SLIM message bus gateway.

Additionally run the observability stack that has OTEL Collector, Grafana and ClickHouse DB.

You can do this by executing the following command:

```sh
docker-compose up slim nats clickhouse-server otel-collector grafana
```

**Step 2: Run the Weather MCP Server**

Start the MCP server, which uses the Nominatim API to convert location names into latitude and longitude coordinates, and then fetches weather data from the Open-Meteo API using those coordinates:

_Local Python Run:_

```sh
uv run python agents/mcp_servers/weather_service.py
```

_Docker Compose:_

```sh
docker-compose up weather-mcp-server --build
```

This MCP server is required for the Colombia Farm to function correctly.

**Step 3A: Run the Farms (via Make targets)**

You can start each server with a `make` target (after running `uv sync` and configuring your `.env`). Open one terminal per service.

Start the Weather MCP (required for Colombia farm):

```sh
make weather-mcp
```

Start farms (each in its own terminal):

```sh
make brazil-farm
make colombia-farm
make vietnam-farm
```

Start the Exchange (Auction Supervisor API):

```sh
make auction-supervisor
```

**Step 3B: Run the Farms (local Python or Docker Compose)**

Start all the farm servers, that act as A2A servers, by executing:

_Local Python Run:_

> **Note:** Each farm should be started in its **own terminal window**

```sh
uv run python agents/farms/brazil/farm_server.py
uv run python agents/farms/colombia/farm_server.py
uv run python agents/farms/vietnam/farm_server.py
```

_Docker Compose:_

```sh
docker-compose up brazil-farm-server colombia-farm-server vietnam-farm-server --build
```

The farm servers handle incoming requests from the exchange and process them using a directed LangGraph containing two directed paths: one for fetching inventory and another for generating orders, depending on the prompt.

**Step 4: Run the Exchange**

Start the exchange, which acts as an A2A client, by running:

_Local Python Run:_

```sh
uv run python agents/supervisors/auction/main.py
```

_Docker Compose:_

```sh
docker-compose up exchange-server --build
```

This command starts a FastAPI server that processes user prompts by passing them to a LangGraph-based supervisor, which manages delegation to worker agents. The supervisor is implemented as a directed LangGraph with nodes for Inventory, Orders, General Information, and Reflection.

Requests that are not related to inventory or order creation are automatically routed to the General Information node, which returns a default response. Inventory requests without a specified farm are broadcast across all farms to collect inventory data. If a specific farm is provided, the request is sent directly to that farm. Order requests are sent one-to-one to a specified farm and must include the farm location and acceptable price.

To invoke the exchange, use the /agent/prompt endpoint to send a human-readable prompt to ask information about coffee inventory or to place an order. For example:

```bash
curl -X POST http://127.0.0.1:8000/agent/prompt \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "How much coffee does the Colombia farm have?"
  }'
```

_Example prompts:_

| Intent                              | Prompt                                                           |
| ----------------------------------- | ---------------------------------------------------------------- |
| Check inventory for a specific farm | How much coffee does the Colombia farm have?                     |
| Check inventory across farms        | Show me the total inventory across all farms.                    |
| Order Request                       | I need 50 lb of coffee beans from Colombia for 0.50 cents per lb |

**Step 5: Access the UI**

Once all services are running, you can access the React UI by starting the frontend development server (from the `exchange/frontend` directory):

_Local Run:_

```sh
npm install
npm run dev
```

_Docker Compose:_

```sh
docker-compose up ui --build
```

By default, the UI will be available at [http://localhost:3000/](http://localhost:3000/).

![Screenshot](images/lungo_ui.png)

### Group Conversation Implementation

Detailed architecture, message flows (SLIM pubsub vs controller channels), service roles, and port configuration are documented in [Group Conversation Docs](./docs/group_conversation.md).


### Observability

#### Trace Visualization via Grafana

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
     [`lungo_dashboard.json`](lungo_dashboard.json)
   - **When prompted, select `grafana-clickhouse-datasource` as the datasource.**
   - Click **"Import"** to add the dashboard.

   ![Screenshot: Import Dashboard](images/grafana_import_dashboard.png)

4. **View Traces for the Lungo Multi-Agent System**

   - Navigate to the imported dashboard.
   - You should see traces and spans generated by the Lungo agents as they process requests.
   - **To view details of a specific trace, click on a TraceID in the dashboard. This will open the full trace and its spans for further inspection.**

   ![Screenshot: OTEL Dashboard](images/dashboard_grafana.png)
   ![Screenshot: OTEL Traces](images/dashboard_traces.png)

---

#### Metrics Computation with AGNTCY's Metrics Computation Engine (MCE)

Details about AGNTCY's MCE can be found in the Telemetry Hub repository: [Metrics Computation Engine](https://github.com/agntcy/telemetry-hub/tree/main/metrics_computation_engine)

1. Run the MCE Components

```sh
docker-compose up metrics-computation-engine mce-api-layer
```

2. Get session IDs within a given time range.

```sh
curl --request GET \
  --url 'http://localhost:8080/traces/sessions?start_time=2025-01-01T00:00:00.000Z&end_time=2030-01-01T11:55:00.000Z'
```

> Note: Update the time range to the desired range.

Example output:

```json
[
	{
		"id": "lungo.exchange_cf39e063-f2f8-4c11-bb52-e2250892ee95",
		"start_timestamp": "2025-09-26T13:36:15.841652Z"
	}
]
```

3. [Optional] Get traces by session ID.

Select one of the session IDs from the previous step, and get traces by session ID with this GET request:

```sh
curl --request GET \
  --url http://localhost:8080/traces/session/lungo.exchange_cf39e063-f2f8-4c11-bb52-e2250892ee95
```

4. Perform metrics computation

A detailed list of supported metrics can be found here: [Supported Metrics](https://github.com/agntcy/telemetry-hub/tree/main/metrics_computation_engine#supported-metrics)

Example request:

```json
{
	"metrics": [
		"AgentToAgentInteractions",
		"AgentToToolInteractions",
		"Cycles",
		"ToolErrorRate",
		"ToolUtilizationAccuracy",
		"GraphDeterminismScore",
		"ComponentConflictRate",
		"Consistency",
		"ContextPreservation",
		"GoalSuccessRate",
		"Groundedness",
		"InformationRetention",
		"IntentRecognitionAccuracy",
		"ResponseCompleteness",
		"WorkflowCohesionIndex",
		"WorkflowEfficiency"
	],
	"data_fetching_infos": {
		"session_ids": [
			"lungo.exchange_cf39e063-f2f8-4c11-bb52-e2250892ee95"
		]
	}
}
```

> Note: this particular session was a result of the prompt: "I'd like to buy 200 lbs quantity of coffee at USD 500 price from Vietnam"
> 
> And agent response: 
> 
> "Your order for 200 lbs of coffee at USD 500 from Vietnam has been successfully created. Here are the details:
>
> - **Order ID:** 54321
> - **Tracking Number:** XYZ789456"
>

Example response:

```json
{
	"metrics": [
		"ToolUtilizationAccuracy",
		"AgentToAgentInteractions",
		"AgentToToolInteractions",
		"Cycles",
		"ToolErrorRate",
		"GraphDeterminismScore",
		"ComponentConflictRate",
		"Consistency",
		"ContextPreservation",
		"GoalSuccessRate",
		"Groundedness",
		"InformationRetention",
		"IntentRecognitionAccuracy",
		"ResponseCompleteness",
		"WorkflowCohesionIndex",
		"WorkflowEfficiency"
	],
	"results": {
		"span_metrics": [
			{
				"metric_name": "ToolUtilizationAccuracy",
				"value": 1.0,
				"aggregation_level": "span",
				"category": "agent",
				"app_name": "lungo.exchange",
				"description": "",
				"reasoning": "The AI agent correctly utilized the 'create_order' tool, as the input requested to create a coffee order with a specific farm ('vietnam'), quantity (200), and price (500). The tool's output confirmed the successful creation of the order, detailing the order ID and tracking number, thus adequately addressing the input. All required arguments were provided and matched the tool definition, making the tool call reasonable and the output useful.",
				"unit": "",
				"span_id": [
					"1f59a724c8e6f2e8"
				],
				"session_id": [
					"lungo.exchange_cf39e063-f2f8-4c11-bb52-e2250892ee95"
				],
				"source": "native",
				"entities_involved": [
					"create_order"
				],
				"edges_involved": [],
				"success": true,
				"metadata": {
					"metric_type": "llm-as-a-judge"
				},
				"error_message": null
			}
		],
		"session_metrics": [
			{
				"metric_name": "AgentToAgentInteractions",
				"value": {},
				"aggregation_level": "session",
				"category": "application",
				"app_name": "lungo.exchange",
				"description": "Agent to agent interaction transition counts",
				"reasoning": "",
				"unit": "transitions",
				"span_id": [
					"07c70d4ce5c52015",
					"4b163c532f7e184f"
				],
				"session_id": [
					"lungo.exchange_cf39e063-f2f8-4c11-bb52-e2250892ee95"
				],
				"source": "native",
				"entities_involved": [
					"vietnam_farm_agent.ainvoke",
					"exchange_agent.serve"
				],
				"edges_involved": [],
				"success": true,
				"metadata": {
					"total_transitions": 0,
					"unique_transitions": 0,
					"all_transitions": []
				},
				"error_message": null
			},
			{
				"metric_name": "AgentToToolInteractions",
				"value": {
					"(Agent: exchange_agent.serve) -> (Tool: create_order)": 1,
					"(Agent: exchange_agent.serve) -> (Tool: unknown)": 1
				},
				"aggregation_level": "session",
				"category": "application",
				"app_name": "lungo.exchange",
				"description": "Agent to tool interaction counts",
				"reasoning": "",
				"unit": "interactions",
				"span_id": [
					"1f59a724c8e6f2e8",
					"bbcb2837bca26146"
				],
				"session_id": [
					"lungo.exchange_cf39e063-f2f8-4c11-bb52-e2250892ee95"
				],
				"source": "native",
				"entities_involved": [
					"unknown",
					"create_order"
				],
				"edges_involved": [],
				"success": true,
				"metadata": {
					"total_tool_calls": 2,
					"unique_interactions": 2
				},
				"error_message": null
			},
			{
				"metric_name": "Cycles",
				"value": 0,
				"aggregation_level": "session",
				"category": "application",
				"app_name": "lungo.exchange",
				"description": "Count of contiguous cycles in agent and tool interactions",
				"reasoning": "Count of contiguous cycles in agent and tool interactions",
				"unit": "cycles",
				"span_id": "",
				"session_id": [
					"lungo.exchange_cf39e063-f2f8-4c11-bb52-e2250892ee95"
				],
				"source": "native",
				"entities_involved": [
					"create_order",
					"vietnam_farm_agent.ainvoke",
					"unknown",
					"exchange_agent.serve"
				],
				"edges_involved": [],
				"success": true,
				"metadata": {
					"span_ids": [
						"07c70d4ce5c52015",
						"1f59a724c8e6f2e8",
						"bbcb2837bca26146",
						"4b163c532f7e184f"
					],
					"event_sequence": [
						"exchange_agent.serve",
						"create_order",
						"unknown",
						"vietnam_farm_agent.ainvoke"
					],
					"total_events": 4
				},
				"error_message": null
			},
			{
				"metric_name": "ToolErrorRate",
				"value": 0.0,
				"aggregation_level": "session",
				"category": "application",
				"app_name": "lungo.exchange",
				"description": "Percentage of tool spans that encountered errors",
				"reasoning": "",
				"unit": "%",
				"span_id": [],
				"session_id": [
					"lungo.exchange_cf39e063-f2f8-4c11-bb52-e2250892ee95"
				],
				"source": "native",
				"entities_involved": [],
				"edges_involved": [],
				"success": true,
				"metadata": {
					"total_tool_calls": 2,
					"total_tool_errors": 0,
					"all_tool_span_ids": [
						"1f59a724c8e6f2e8",
						"bbcb2837bca26146"
					]
				},
				"error_message": null
			},
			{
				"metric_name": "ComponentConflictRate",
				"value": 1.0,
				"aggregation_level": "session",
				"category": "application",
				"app_name": "lungo.exchange",
				"description": "",
				"reasoning": "Both responses indicate successful order creation without mentioning any conflicts or discrepancies between the components involved. The system's functionality appears smooth with no reference to any interruptions or inconsistencies in data, logic, or execution. Consequently, these elements suggest a harmonious operation where components do not interfere with each other, aligning with a score of 1 according to the rubric.",
				"unit": "",
				"span_id": [
					"07c70d4ce5c52015",
					"4b163c532f7e184f"
				],
				"session_id": [
					"lungo.exchange_cf39e063-f2f8-4c11-bb52-e2250892ee95"
				],
				"source": "native",
				"entities_involved": [
					"exchange_agent.serve",
					"vietnam_farm_agent.ainvoke"
				],
				"edges_involved": [],
				"success": true,
				"metadata": {
					"metric_type": "llm-as-a-judge"
				},
				"error_message": null
			},
			{
				"metric_name": "Consistency",
				"value": 1.0,
				"aggregation_level": "session",
				"category": "application",
				"app_name": "lungo.exchange",
				"description": "",
				"reasoning": "Both responses consistently convey that an order for coffee has been placed. Details of the order, including the Order ID and Tracking Number, are the same in both responses, indicating consistency in the information provided. There are no contradictions or conflicting statements across the responses. Additionally, the tone and style are cordial and efficient, maintaining consistency throughout. Therefore, the interactions are fully consistent based on the evaluation criteria.",
				"unit": "",
				"span_id": [
					"07c70d4ce5c52015",
					"4b163c532f7e184f"
				],
				"session_id": [
					"lungo.exchange_cf39e063-f2f8-4c11-bb52-e2250892ee95"
				],
				"source": "native",
				"entities_involved": [
					"exchange_agent.serve",
					"vietnam_farm_agent.ainvoke"
				],
				"edges_involved": [],
				"success": true,
				"metadata": {
					"metric_type": "llm-as-a-judge"
				},
				"error_message": null
			},
			{
				"metric_name": "ContextPreservation",
				"value": 1.0,
				"aggregation_level": "session",
				"category": "application",
				"app_name": "lungo.exchange",
				"description": "",
				"reasoning": "The responses accurately address the inputs by confirming the creation of the orders with specified details. They maintain relevance by providing order IDs and tracking numbers, continuing the context of order confirmations. The structure is logical, listing order details and offering further assistance. Although additional context from the initial inputs is missing, the essential information is conveyed effectively. The responses are useful as they confirm successful order processing, fulfilling the user's request.",
				"unit": "",
				"span_id": [
					"07c70d4ce5c52015",
					"4b163c532f7e184f"
				],
				"session_id": [
					"lungo.exchange_cf39e063-f2f8-4c11-bb52-e2250892ee95"
				],
				"source": "native",
				"entities_involved": [
					"exchange_agent.serve",
					"vietnam_farm_agent.ainvoke"
				],
				"edges_involved": [],
				"success": true,
				"metadata": {
					"metric_type": "llm-as-a-judge"
				},
				"error_message": null
			},
			{
				"metric_name": "GoalSuccessRate",
				"value": 1.0,
				"aggregation_level": "session",
				"category": "application",
				"app_name": "lungo.exchange",
				"description": "",
				"reasoning": "The response accurately corresponds to the user's goal by confirming the successful creation of an order for 200 lbs of coffee at USD 500 from Vietnam. It provides relevant details, including an Order ID and a Tracking Number, fulfilling the expectations of the query. Although the response could state the reasons if it cannot achieve the goal, in this case, it appears the goal is met without issue.",
				"unit": "",
				"span_id": [
					"4cd8bc7ec2badea2",
					"a3bba979a31de5c5",
					"530ad7dd5dcf4795",
					"666396ef1015e0b0",
					"8f360cd51cde700f",
					"c6325c8193105315"
				],
				"session_id": [
					"lungo.exchange_cf39e063-f2f8-4c11-bb52-e2250892ee95"
				],
				"source": "native",
				"entities_involved": [
					"exchange_agent.serve",
					"vietnam_farm_agent.ainvoke"
				],
				"edges_involved": [],
				"success": true,
				"metadata": {
					"metric_type": "llm-as-a-judge"
				},
				"error_message": null
			},
			{
				"metric_name": "Groundedness",
				"value": 1.0,
				"aggregation_level": "session",
				"category": "application",
				"app_name": "lungo.exchange",
				"description": "",
				"reasoning": "The responses consistently refer to contextual elements like order creation and tracking information, and avoid providing speculative or unsupported details. Without external verification tools or integration evidence visible, there's no way to confirm whether details like Order ID and Tracking Number are genuinely linked to real-time data, but they remain consistent with the input prompts and maintain factual accuracy. Thus, the responses are considered grounded in the given context.",
				"unit": "",
				"span_id": "",
				"session_id": "lungo.exchange_cf39e063-f2f8-4c11-bb52-e2250892ee95",
				"source": "native",
				"entities_involved": [
					"exchange_agent.serve",
					"vietnam_farm_agent.ainvoke"
				],
				"edges_involved": [],
				"success": true,
				"metadata": {
					"span_ids": [
						"07c70d4ce5c52015",
						"4b163c532f7e184f"
					]
				},
				"error_message": null
			},
			{
				"metric_name": "InformationRetention",
				"value": 1.0,
				"aggregation_level": "session",
				"category": "application",
				"app_name": "lungo.exchange",
				"description": "",
				"reasoning": "The Assistant successfully retains details from the earlier purchase request, consistently referencing order ID 54321 and tracking number XYZ789456 across interactions. This demonstrates accurate recall of key details without inconsistencies. The responses are coherent and the recalled information is relevant and appropriately applied. Therefore, based on the rubric criteria, the Assistant's information retention and recall performance is satisfactory.",
				"unit": "",
				"span_id": [
					"07c70d4ce5c52015",
					"4b163c532f7e184f"
				],
				"session_id": [
					"lungo.exchange_cf39e063-f2f8-4c11-bb52-e2250892ee95"
				],
				"source": "native",
				"entities_involved": [
					"exchange_agent.serve",
					"vietnam_farm_agent.ainvoke"
				],
				"edges_involved": [],
				"success": true,
				"metadata": {
					"metric_type": "llm-as-a-judge"
				},
				"error_message": null
			},
			{
				"metric_name": "IntentRecognitionAccuracy",
				"value": 1.0,
				"aggregation_level": "session",
				"category": "application",
				"app_name": "lungo.exchange",
				"description": "",
				"reasoning": "The response accurately identifies the user's intent to place an order for 200 lbs of coffee from Vietnam at a specific price. It addresses this intent by confirming the order creation and providing specific order details such as Order ID and Tracking Number. The response is appropriate as it confirms the action taken and offers further assistance, aligning well with the user's intent.",
				"unit": "",
				"span_id": [
					"07c70d4ce5c52015",
					"4b163c532f7e184f"
				],
				"session_id": [
					"lungo.exchange_cf39e063-f2f8-4c11-bb52-e2250892ee95"
				],
				"source": "native",
				"entities_involved": [
					"exchange_agent.serve",
					"vietnam_farm_agent.ainvoke"
				],
				"edges_involved": [],
				"success": true,
				"metadata": {
					"metric_type": "llm-as-a-judge"
				},
				"error_message": null
			},
			{
				"metric_name": "ResponseCompleteness",
				"value": 1.0,
				"aggregation_level": "session",
				"category": "application",
				"app_name": "lungo.exchange",
				"description": "",
				"reasoning": "Both responses effectively address the user's query, confirming the creation of coffee orders with specified details such as price, quantity, and providing order ID and tracking number. While there is no explicit mention of Vietnam in the second response, the order creation details are consistent. Sufficient detail is provided for order confirmation; therefore, no critical information is omitted.",
				"unit": "",
				"span_id": [
					"07c70d4ce5c52015",
					"4b163c532f7e184f"
				],
				"session_id": [
					"lungo.exchange_cf39e063-f2f8-4c11-bb52-e2250892ee95"
				],
				"source": "native",
				"entities_involved": [
					"exchange_agent.serve",
					"vietnam_farm_agent.ainvoke"
				],
				"edges_involved": [],
				"success": true,
				"metadata": {
					"metric_type": "llm-as-a-judge"
				},
				"error_message": null
			},
			{
				"metric_name": "WorkflowCohesionIndex",
				"value": 1.0,
				"aggregation_level": "session",
				"category": "application",
				"app_name": "lungo.exchange",
				"description": "",
				"reasoning": "Both workflow responses exhibit a high level of cohesion. The components interact smoothly without any noticeable friction, and there is a logical flow from order creation to order confirmation. The presence of detailed order information, such as order ID and tracking number, maintains consistency and efficiency across the workflow stages. This indicates seamless integration among components.",
				"unit": "",
				"span_id": [
					"07c70d4ce5c52015",
					"4b163c532f7e184f"
				],
				"session_id": [
					"lungo.exchange_cf39e063-f2f8-4c11-bb52-e2250892ee95"
				],
				"source": "native",
				"entities_involved": [
					"vietnam_farm_agent.ainvoke",
					"exchange_agent.serve"
				],
				"edges_involved": [],
				"success": true,
				"metadata": {
					"metric_type": "llm-as-a-judge"
				},
				"error_message": null
			}
		],
		"population_metrics": []
	}
}
```