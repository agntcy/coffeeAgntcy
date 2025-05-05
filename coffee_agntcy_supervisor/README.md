# Acorda Supervisor Agent

This agent was built with **FastAPI**, that can operate using:

- A **standard API** compatible with [LangChain’s Agent Protocol](https://github.com/langchain-ai/agent-protocol) — an open-source framework for interfacing with AI agents.
- A **direct application mode** for invoking the SupervisorGraph without running a server.

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

### **Run Modes**

#### **1️⃣ Server Mode**

You can run the application in server mode by executing:

```bash
make run-server
```
or
```bash
python supervisor/main.py --server
```

#### **2️⃣ Direct Application Mode**

To invoke the SupervisorGraph directly without running a server, execute:

```bash
make run
```

---

### Expected Console Output

#### **Server Mode**
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

#### **Direct Application Mode**
When running in direct application mode, you should see the output of the SupervisorGraph execution, such as:

```bash
SupervisorGraph result: Successfully processed the coffee farm request.
```

---

### REST Client
To test the server, you can use the provided REST client.
*Change to `clients` folder*

*Update the user_prompt in `test_clients/ap_client/client.py` to the desired prompt (sample prompts available in `clients/sample_prompts/`*

The REST client connects to the AP endpoint for the Server running at the default port 8125.

```bash
python test_clients/ap_client/client.py
```