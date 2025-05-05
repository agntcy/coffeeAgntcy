# Acorda Supervisor Agent

This agent was built with **FastAPI**, that can operate using:

- A **standard API** compatible with [LangChain’s Agent Protocol](https://github.com/langchain-ai/agent-protocol) — an open-source framework for interfacing with AI agents.
- A **ACP complaint agent interface** using [Agntcy ACP Protocol](https://spec.acp.agntcy.org/#/) — an open-source protocol for interfacing with AI agents.
---

## **📋 Prerequisites**
Before installation, ensure you have:
- **Python 3.12+** installed
- A **virtual environment** (recommended for dependency isolation)

---
## **⚙️ Installation Steps**

### **1️⃣ Clone the Repository**

```bash
git clone https://github.com/cisco-outshift-ai-agents/acorda.git
cd acorda/coffee_agntcy_supervisor
```
---
### **2️⃣ Setup the environment variables**

### Required Environment Variables
Before running the application, ensure you have the following environment variables set in your .env file or in your environment:

#### **🔹 OpenAI or Azure OpenAI API Configuration**

You can configure your AI agent to use either OpenAI or Azure OpenAI as its LLM provider.
Set the appropriate variables based on your choice (if unspecified , defaults to 'azure'):
```bash
LLM_PROVIDER=azure # or openai
```

For OpenAI:
```bash
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_API_VERSION=gpt-4o  # Specify the model name
OPENAI_TEMPERATURE=0.7    # Adjust temperature for response randomness
```

For Azure OpenAI:
```bash
AZURE_OPENAI_API_KEY=your-azure-api-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=your-deployment-name  # Deployment name in Azure
AZURE_OPENAI_API_VERSION=your-azure-openai-api-version  # API version
OPENAI_TEMPERATURE=0.7 # Adjust temperature for response randomness
```

#### **🔹 LangChain Configuration(Optional)**
Export these environment variables to integrate Langchain tracing and observability functionalities for your agent.
```bash
LANGCHAIN_TRACING_V2=true  # Enable LangChain tracing
LANGCHAIN_ENDPOINT=your-langchain-endpoint  # The LangChain API endpoint
LANGCHAIN_API_KEY=your-langchain-api-key   # API key for LangChain
LANGCHAIN_PROJECT=your-langchain-project-name  # Project name in LangChain
LANGSMITH_API_KEY=your-langsmith-api-key   # API key for LangSmith
```

---
### **3️⃣ Setup the virtual environment**
Note: poetry is required for this step. If you don't have it installed, you can install it using `brew install poetry`.
```bash
python -m venv venv
source venv/bin/activate
poetry install
```
---
✅ **Now you're ready to run the application!**
### Server

You can run the application by executing:

```bash
make run
```
or
```bash
python supervisor/main.py
```
### Expected Console Output

On a successful run, you should see logs in your terminal similar to the snippet below. The exact timestamps, process IDs, and file paths will vary:

```bash
INFO:     Started server process [62981]
INFO:     Waiting for application startup.
2025-05-02 17:04:43 [root] [INFO] [lifespan] Starting Acorda Supervisor Agent...
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8125 (Press CTRL+C to quit)
```

This output confirms that:

1. Logging is properly initialized.
2. The server is listening on `0.0.0.0:8125`.
3. Your environment variables (like `.env file loaded`) are read.

### AP REST Client

*Change to `clients` folder*

*Update the user_prompt in `test_clients/ap_client/client.py` to the desired prompt (sample prompts available in `clients/sample_prompts/`*

The REST client connects to the AP endpoint for the Server running at the default port 8125

```bash
python test_clients/ap_client/client.py
```
On a successful remote graph run you should see logs in your terminal similar to the snippet below:

```bash
{"timestamp": "2025-03-14 17:58:29,328", "level": "INFO", "message": "{'event': 'final_result', 'result': {'messages': [HumanMessage(content='is Alfred Plus Test a business project', additional_kwargs={}, response_metadata={}, id='6ddcc789-0196-4e24-86fc-f2119be43cdf'), HumanMessage(content='The project \"Alfred Plus Test\" is a software project, not a business project.', additional_kwargs={}, response_metadata={}, id='140ef897-cdb6-459d-914c-b5d2d2fd8281')]}}", "module": "rest", "function": "main", "line": 203, "logger": "graph_client", "pid": 51728}
```

Sample API request and response for running a remote graph AP request can be sent via:

*http://0.0.0.0:8125/docs#/Stateless%20Runs/Stateless%20Runs-run_stateless_runs_post*

```bash
curl -X 'POST' \
  'http://0.0.0.0:8125/api/v1/runs' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "agent_id": "remote_agent",
    "input": {
        "query": "Need 100 tons of Arabica roast from Vietnam region by December 15"
    },
    "metadata": {
        "id": "c303282d-f2e6-46ca-a04a-35d3d873712d"
    }
}'

200 OK
{
  "agent_id": "remote_agent",
  "output": "Successfully processed the coffee farm request",
  "model": "gpt-4o",
  "metadata": {}
}
```

---
### ACP Client (using the agent deployed via Workflow server Manager)

#### PreRequisites
The agent must be deployed using Workflow Server Manager following [these instructions](https://github.com/cisco-outshift-ai-agents/acorda/blob/main/coffee_exchange_supervisor/deploy_acp/README.md).

Detailed instruction on running the clients with this agent are available [here](https://github.com/cisco-outshift-ai-agents/acorda/blob/main/coffee_exchange_supervisor/deploy_acp/README.md).

*Change to `clients` folder*

*Depending on the specific client to be run, Update the user_prompt in `clients/acp_client/client_*.py` to the desired prompt (sample prompts available in `clients/sample_prompts/`*

*Update the env variables in .env per clients/acp_client/.env.sample*

Run either of the clients provided. Eg.
```bash
python test_clients/acp_client/client_async.py
```

## API Endpoints

By default, the API documentation is available at:

```bash
http://0.0.0.0:8125/docs
```

(Adjust the host and port if you override them via environment variable ACORDA_AGENT_PORT.)

---
## Running as a LangGraph Studio

You need to install Rust: <https://www.rust-lang.org/tools/install>

Run the server

*To see the graph for the end client using LangGraph AP*
```bash
make graph-ap
```

*To see the graph for the entire workflow*
```bash
make langgraph-dev
```
---
## Running Unit and Evaluation Tests

To run the tests or eval tests, you need to set up the environment variables and then execute the respective test command.

1. **Set the Environment Variables**:  
   Add the required variables to your `.env` file or export them directly in your shell.

   Example `.env` file or export these environment variables directly in your shell:
   ```bash
   LANGCHAIN_API_KEY=your-langsmith-api-key
   # OpenAI Configuration
   OPENAI_ENDPOINT=https://api.openai.com/v1
   OPENAI_API_KEY=your-openai-api-key
   # Alternatively, for Azure OpenAI
   AZURE_OPENAI_ENDPOINT=https://your-azure-endpoint.openai.azure.com
   AZURE_OPENAI_API_KEY=your-azure-api-key
   AZURE_OPENAI_API_VERSION=2023-03-15-preview
   AZURE_OPENAI_DEPLOYMENT=gpt-4o
   
   LLM_PROVIDER=azure # or openai
   ```

---
## Roadmap

See the [open issues](https://github.com/cisco-outshift-ai-agents/acorda/issues) for a list
of proposed features (and known issues).

---
## Contributing

Contributions are what make the open source community such an amazing place to
learn, inspire, and create. Any contributions you make are **greatly
appreciated**. For detailed contributing guidelines, please see
[CONTRIBUTING.md](CONTRIBUTING.md)

Please ensure commits conform to the [Commit Guideline](https://www.conventionalcommits.org/en/v1.0.0/ )
