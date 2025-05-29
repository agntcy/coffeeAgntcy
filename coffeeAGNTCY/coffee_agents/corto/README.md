# Corto Exchange, Farm Server, UI

## Overview

The Corto demo demonstrates a robust interaction between an A2A (Agent-to-Agent) architecture and LangGraph workflows. The `farm_server` operates as an A2A agent, providing backend services to process user inputs and generate coffee flavor profiles. The `exchange` acts as an A2A client, connecting to the `farm_server` and facilitating user interactions. Both components are integrated within LangGraph, which manages stateful workflows and ensures seamless communication.

## UI Component 

The project includes a **React-based UI** for interacting with the exchange and farm server.  


## Trying the Corto App

You can use Corto in two ways:

1. **Local Testing Setup**  
   Run each component (farm server, exchange, and UI) directly on your machine for development/debugging.

2. **Docker Compose Setup**  
   Quickly spin up all components (farm server, exchange, and UI) as containers using Docker Compose.

See the sections below for step-by-step instructions for each approach.

## Local testing Setup:


### Prerequisites

Ensure you have `uv` installed. You can install it using Homebrew:

```sh
brew install uv
```

Ensure your **Node.js** version is **16.14.0** or higher. Check your version with:
  ```sh
  node -v
  ```
If Node.js is not installed, download and install it from the [official website](https://nodejs.org/).

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

3. **Configure Environment Variables:**
    Copy the `.env.example` file to `.env`:

    ```sh
    cp .env.example .env
    ```

    Add your LLM provider (OpenAI or Azure OpenAI) and associated credentials to the .env file. For example:
 
   ```env
    LLM_PROVIDER=openai
    OPENAI_API_KEY=your_openai_api_key
    OPENAI_MODEL=gpt-4o
    ```

   Or for Azure OpenAI:

    ```env
    LLM_PROVIDER=azure
    AZURE_OPENAI_ENDPOINT=https://your-azure-resource.openai.azure.com/
    AZURE_OPENAI_DEPLOYMENT=gpt-4-prod
    AZURE_OPENAI_API_KEY=your_azure_api_key
    AZURE_OPENAI_API_VERSION=2023-12-01-preview
    ```

3. **Verify Setup:**
   Ensure everything is set up correctly by running the farm server, exchange and UI as described below.

### Execution

#### Step 1: Run the Farm Server
Start the `farm_server`, which acts as an A2A agent, by executing:

```sh
uv run python farm/farm_server.py
```

The `farm_server` listens for requests from the `exchange` and processes them using LangGraph. It generates flavor profiles based on user inputs such as location and season.

#### Step 2: Run the Exchange
Start the `exchange`, which acts as an A2A client, by running:

```sh
uv run python exchange/main.py
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


#### Step 3: Access the UI

Once the backend and farm server are running, you can access the React UI by starting the frontend development server (from the `exchange/frontend` directory):

```sh
npm install
npm run dev
```

By default, the UI will be available at [http://localhost:3000/](http://localhost:3000/).



## Docker Compose Setup:

**Prerequisite:**
Before running Docker Compose, copy the example environment file and fill in your credentials:

```sh
cp .env.example .env
```

Edit the `.env` file to include your LLM provider and API keys (OpenAI or Azure OpenAI), for example:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o
```
or for Azure:
```env
LLM_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://your-azure-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4-prod
AZURE_OPENAI_API_KEY=your_azure_api_key
AZURE_OPENAI_API_VERSION=2023-12-01-preview
```

**Authenticate to GHCR to pull private images:**

```sh
echo "<git_token>" | docker login ghcr.io -u "<git_user>" --password-stdin
```
Replace `<git_token>` and `<git_user>` with your GitHub token and username.

**Start the stack:**

```sh
docker compose up
```

Once running, access the UI at: [http://localhost:3000/](http://localhost:3000/)

---


![Screenshot](images/corto-ui.png)

