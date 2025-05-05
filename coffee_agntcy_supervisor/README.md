# Acorda Supervisor Agent

This agent was built with **FastAPI**, that can operate using:

- A **standard API** compatible with [LangChain’s Agent Protocol](https://github.com/langchain-ai/agent-protocol) — an open-source framework for interfacing with AI agents.
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