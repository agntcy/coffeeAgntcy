
<!-- TOC -->
* [Corto Exchange, Farm Server, UI](#corto-exchange-farm-server-ui)
  * [Overview](#overview)
  * [Running Corto Locally](#running-corto-locally)
    * [Prerequisites](#prerequisites)
    * [Setup Instructions](#setup-instructions)
    * [Execution](#execution)
    * [Observability](#observability)
      * [Trace Visualization via Grafana](#trace-visualization-via-grafana)
      * [Metrics Computation with AGNTCY's Metrics Computation Engine (MCE)](#metrics-computation-with-agntcys-metrics-computation-engine-mce)
<!-- TOC -->

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
		"id": "corto.exchange_c4a5371e-5d3f-4602-a5c8-05c6321fbe89",
		"start_timestamp": "2025-10-02T20:16:21.879278097Z"
	}
]
```

3. [Optional] Get traces by session ID.

Select one of the session IDs from the previous step, and get traces by session ID with this GET request:

```sh
curl --request GET \
  --url http://localhost:8080/traces/session/corto.exchange_c4a5371e-5d3f-4602-a5c8-05c6321fbe89
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
			"corto.exchange_c4a5371e-5d3f-4602-a5c8-05c6321fbe89"
		]
	}
}
```

> Note: this particular session was a result of the following prompt: "What are the flavor profiles of Ethiopian coffee?"
> 
> And agent response: "Ethiopian coffee is known for its bright acidity with floral and citrus notes, a light to medium body, and a complex, aromatic finish."

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
				"app_name": "corto.exchange",
				"description": "",
				"reasoning": "The tool 'transfer_to_get_flavor_profile_via_a2a' was called to address the input query about Ethiopian coffee flavor profiles. The tool's purpose aligns with the query as it asks another agent for this specialized information. The tool call was successful and transferred the request as intended, which directly relates to the input's needs. Thus, the tool call was reasonable and provided a satisfactory outcome in line with the task requirements.",
				"unit": "",
				"span_id": [
					"602f08c390c47c65"
				],
				"session_id": [
					"corto.exchange_c4a5371e-5d3f-4602-a5c8-05c6321fbe89"
				],
				"source": "native",
				"entities_involved": [
					"transfer_to_get_flavor_profile_via_a2a"
				],
				"edges_involved": [],
				"success": true,
				"metadata": {
					"metric_type": "llm-as-a-judge"
				},
				"error_message": null
			},
			{
				"metric_name": "ToolUtilizationAccuracy",
				"value": 1.0,
				"aggregation_level": "span",
				"category": "agent",
				"app_name": "corto.exchange",
				"description": "",
				"reasoning": "The tool 'get_flavor_profile' was appropriately called to estimate the flavor profile of Ethiopian coffee based on the input prompt provided. The tool successfully output a detailed flavor profile characterized by bright acidity, floral and citrus notes, a light to medium body, and a complex, aromatic finish. This directly addresses the input query regarding the flavor profile, making the tool call reasonable and effective.",
				"unit": "",
				"span_id": [
					"f7ef5efaa25a39ef"
				],
				"session_id": [
					"corto.exchange_c4a5371e-5d3f-4602-a5c8-05c6321fbe89"
				],
				"source": "native",
				"entities_involved": [
					"get_flavor_profile"
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
				"app_name": "corto.exchange",
				"description": "Agent to agent interaction transition counts",
				"reasoning": "",
				"unit": "transitions",
				"span_id": [
					"2f5b0d7e13d7369f",
					"bfa685f44c2f93f5",
					"6c6fe3ab6c1a53f1"
				],
				"session_id": [
					"corto.exchange_c4a5371e-5d3f-4602-a5c8-05c6321fbe89"
				],
				"source": "native",
				"entities_involved": [
					"farm_agent.flavor_node",
					"farm_agent.ainvoke",
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
					"(Agent: exchange_agent.serve) -> (Tool: transfer_to_get_flavor_profile_via_a2a)": 1,
					"(Agent: exchange_agent.serve) -> (Tool: get_flavor_profile)": 1,
					"(Agent: exchange_agent.serve) -> (Tool: unknown)": 1
				},
				"aggregation_level": "session",
				"category": "application",
				"app_name": "corto.exchange",
				"description": "Agent to tool interaction counts",
				"reasoning": "",
				"unit": "interactions",
				"span_id": [
					"602f08c390c47c65",
					"f7ef5efaa25a39ef",
					"132b8cd82bf2532a"
				],
				"session_id": [
					"corto.exchange_c4a5371e-5d3f-4602-a5c8-05c6321fbe89"
				],
				"source": "native",
				"entities_involved": [
					"unknown",
					"get_flavor_profile",
					"transfer_to_get_flavor_profile_via_a2a"
				],
				"edges_involved": [],
				"success": true,
				"metadata": {
					"total_tool_calls": 3,
					"unique_interactions": 3
				},
				"error_message": null
			},
			{
				"metric_name": "Cycles",
				"value": 0,
				"aggregation_level": "session",
				"category": "application",
				"app_name": "corto.exchange",
				"description": "Count of contiguous cycles in agent and tool interactions",
				"reasoning": "Count of contiguous cycles in agent and tool interactions",
				"unit": "cycles",
				"span_id": "",
				"session_id": [
					"corto.exchange_c4a5371e-5d3f-4602-a5c8-05c6321fbe89"
				],
				"source": "native",
				"entities_involved": [
					"get_flavor_profile",
					"unknown",
					"farm_agent.ainvoke",
					"farm_agent.flavor_node",
					"transfer_to_get_flavor_profile_via_a2a",
					"exchange_agent.serve"
				],
				"edges_involved": [],
				"success": true,
				"metadata": {
					"span_ids": [
						"2f5b0d7e13d7369f",
						"602f08c390c47c65",
						"f7ef5efaa25a39ef",
						"132b8cd82bf2532a",
						"bfa685f44c2f93f5",
						"6c6fe3ab6c1a53f1"
					],
					"event_sequence": [
						"exchange_agent.serve",
						"transfer_to_get_flavor_profile_via_a2a",
						"get_flavor_profile",
						"unknown",
						"farm_agent.ainvoke",
						"farm_agent.flavor_node"
					],
					"total_events": 6
				},
				"error_message": null
			},
			{
				"metric_name": "ToolErrorRate",
				"value": 0.0,
				"aggregation_level": "session",
				"category": "application",
				"app_name": "corto.exchange",
				"description": "Percentage of tool spans that encountered errors",
				"reasoning": "",
				"unit": "%",
				"span_id": [],
				"session_id": [
					"corto.exchange_c4a5371e-5d3f-4602-a5c8-05c6321fbe89"
				],
				"source": "native",
				"entities_involved": [],
				"edges_involved": [],
				"success": true,
				"metadata": {
					"total_tool_calls": 3,
					"total_tool_errors": 0,
					"all_tool_span_ids": [
						"602f08c390c47c65",
						"f7ef5efaa25a39ef",
						"132b8cd82bf2532a"
					]
				},
				"error_message": null
			},
			{
				"metric_name": "ComponentConflictRate",
				"value": 1.0,
				"aggregation_level": "session",
				"category": "application",
				"app_name": "corto.exchange",
				"description": "",
				"reasoning": "All responses show a clear relationship between components without apparent conflicts or inconsistencies. Each interaction correctly results in flavor notes of Ethiopian coffee without disruption. The data is consistent across different input formulations, exhibiting no contradictions or interference in functionality. Therefore, the components appear to work smoothly in harmony.",
				"unit": "",
				"span_id": [
					"2f5b0d7e13d7369f",
					"bfa685f44c2f93f5",
					"6c6fe3ab6c1a53f1"
				],
				"session_id": [
					"corto.exchange_c4a5371e-5d3f-4602-a5c8-05c6321fbe89"
				],
				"source": "native",
				"entities_involved": [
					"exchange_agent.serve",
					"farm_agent.ainvoke",
					"farm_agent.flavor_node"
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
				"app_name": "corto.exchange",
				"description": "",
				"reasoning": "The responses consistently describe Ethiopian coffee as having bright acidity, floral and citrus notes, a light to medium body, and a complex, aromatic finish. There are no contradictions or conflicting statements across the given interactions. The tone and style remain consistent, focusing on factual flavor attributes. Therefore, the responses fully meet the consistency criteria.",
				"unit": "",
				"span_id": [
					"2f5b0d7e13d7369f",
					"bfa685f44c2f93f5",
					"6c6fe3ab6c1a53f1"
				],
				"session_id": [
					"corto.exchange_c4a5371e-5d3f-4602-a5c8-05c6321fbe89"
				],
				"source": "native",
				"entities_involved": [
					"exchange_agent.serve",
					"farm_agent.ainvoke",
					"farm_agent.flavor_node"
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
				"app_name": "corto.exchange",
				"description": "",
				"reasoning": "All responses accurately understand and address the input by describing the flavor profile of Ethiopian coffee consistently throughout the conversation. The responses are relevant, logically structured, and provide insightful information about the specific flavor notes, which include bright acidity, floral and citrus notes, a light to medium body, and a complex, aromatic finish. Each response maintains the context and offers useful information regarding the inquiry into Ethiopian coffee flavors.",
				"unit": "",
				"span_id": [
					"2f5b0d7e13d7369f",
					"bfa685f44c2f93f5",
					"6c6fe3ab6c1a53f1"
				],
				"session_id": [
					"corto.exchange_c4a5371e-5d3f-4602-a5c8-05c6321fbe89"
				],
				"source": "native",
				"entities_involved": [
					"exchange_agent.serve",
					"farm_agent.ainvoke",
					"farm_agent.flavor_node"
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
				"app_name": "corto.exchange",
				"description": "",
				"reasoning": "The response effectively describes the flavor profiles of Ethiopian coffee, highlighting its bright acidity, floral and citrus notes, light to medium body, and complex, aromatic finish. These elements align well with the typical characteristics associated with Ethiopian coffee, fulfilling the expectations of the goal expressed in the query.",
				"unit": "",
				"span_id": [
					"36b875efec37c545",
					"387d0c4b9cecce2b",
					"e6e373286caea707",
					"efd56df8f596627c",
					"990bdb006308b18f"
				],
				"session_id": [
					"corto.exchange_c4a5371e-5d3f-4602-a5c8-05c6321fbe89"
				],
				"source": "native",
				"entities_involved": [
					"exchange_agent.serve",
					"farm_agent.ainvoke",
					"farm_agent.flavor_node"
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
				"app_name": "corto.exchange",
				"description": "",
				"reasoning": "The response regarding Ethiopian coffee's flavor profile is fully grounded in the provided input data. It accurately repeats the flavor notes mentioned in multiple outputs, maintaining consistency and factual accuracy. There is no evidence of speculation, hallucination, or misleading statements throughout the responses, adhering strictly to verifiable information.",
				"unit": "",
				"span_id": "",
				"session_id": "corto.exchange_c4a5371e-5d3f-4602-a5c8-05c6321fbe89",
				"source": "native",
				"entities_involved": [
					"exchange_agent.serve",
					"farm_agent.ainvoke",
					"farm_agent.flavor_node"
				],
				"edges_involved": [],
				"success": true,
				"metadata": {
					"span_ids": [
						"2f5b0d7e13d7369f",
						"bfa685f44c2f93f5",
						"6c6fe3ab6c1a53f1"
					]
				},
				"error_message": null
			},
			{
				"metric_name": "InformationRetention",
				"value": 1.0,
				"aggregation_level": "session",
				"category": "application",
				"app_name": "corto.exchange",
				"description": "",
				"reasoning": "The Assistant effectively retains and recalls information about the Ethiopian coffee flavor profile across all interactions. The responses are consistent, correctly referencing the same details about bright acidity, floral and citrus notes, light to medium body, and aromatic finish. There are no inconsistencies or omissions noted in any interaction, indicating accurate and reliable information retention and recall.",
				"unit": "",
				"span_id": [
					"2f5b0d7e13d7369f",
					"bfa685f44c2f93f5",
					"6c6fe3ab6c1a53f1"
				],
				"session_id": [
					"corto.exchange_c4a5371e-5d3f-4602-a5c8-05c6321fbe89"
				],
				"source": "native",
				"entities_involved": [
					"exchange_agent.serve",
					"farm_agent.ainvoke",
					"farm_agent.flavor_node"
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
				"app_name": "corto.exchange",
				"description": "",
				"reasoning": "The response accurately identifies the user's intent, which is to learn about the flavor profiles of Ethiopian coffee. It correctly addresses this intent by providing specific flavor characteristics such as bright acidity, floral and citrus notes, a light to medium body, and a complex, aromatic finish. This response is appropriate for the identified intent as it gives direct and detailed information about Ethiopian coffee flavors.",
				"unit": "",
				"span_id": [
					"2f5b0d7e13d7369f",
					"bfa685f44c2f93f5",
					"6c6fe3ab6c1a53f1"
				],
				"session_id": [
					"corto.exchange_c4a5371e-5d3f-4602-a5c8-05c6321fbe89"
				],
				"source": "native",
				"entities_involved": [
					"exchange_agent.serve",
					"farm_agent.ainvoke",
					"farm_agent.flavor_node"
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
				"app_name": "corto.exchange",
				"description": "",
				"reasoning": "All responses consistently describe Ethiopian coffee's flavor profile, covering aspects like acidity, floral and citrus notes, body, and aromatic finish. The responses cover all relevant aspects of the user's query and provide sufficient detail, ensuring no critical information is omitted. Each response achieves completeness by addressing the flavor profile thoroughly as required by the user query.",
				"unit": "",
				"span_id": [
					"2f5b0d7e13d7369f",
					"bfa685f44c2f93f5",
					"6c6fe3ab6c1a53f1"
				],
				"session_id": [
					"corto.exchange_c4a5371e-5d3f-4602-a5c8-05c6321fbe89"
				],
				"source": "native",
				"entities_involved": [
					"exchange_agent.serve",
					"farm_agent.ainvoke",
					"farm_agent.flavor_node"
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
				"app_name": "corto.exchange",
				"description": "",
				"reasoning": "The components within the workflow display a high level of cohesion and integration. Each component logically follows the other with minimal friction, and they maintain a consistent flow throughout each stage. This is evidenced by the effective transition of data and tasks across nodes, efficient handling of attributes, and coherent output generation. There is no indication of inconsistencies or inefficiencies in the workflow's design or execution. Therefore, the workflow can be considered highly cohesive.",
				"unit": "",
				"span_id": [
					"2f5b0d7e13d7369f",
					"bfa685f44c2f93f5",
					"6c6fe3ab6c1a53f1"
				],
				"session_id": [
					"corto.exchange_c4a5371e-5d3f-4602-a5c8-05c6321fbe89"
				],
				"source": "native",
				"entities_involved": [
					"farm_agent.flavor_node",
					"farm_agent.ainvoke",
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