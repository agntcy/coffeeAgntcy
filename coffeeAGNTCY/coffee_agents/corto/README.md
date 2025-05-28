# Corto Exchange and Farm Server

## Overview

The Corto demo demonstrates a robust interaction between an A2A (Agent-to-Agent) architecture and LangGraph workflows. The `farm_server` operates as an A2A agent, providing backend services to process user inputs and generate coffee flavor profiles. The `exchange` acts as an A2A client, connecting to the `farm_server` and facilitating user interactions. Both components are integrated within LangGraph, which manages stateful workflows and ensures seamless communication.

## Prerequisites

Ensure you have `uv` installed. You can install it using Homebrew:

```sh
brew install uv
```

## Setup

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

    Populate the `.env` file with your OpenAI or Azure OpenAI credentials. For example:

    ```env
    OPENAI_API_KEY=your_openai_api_key
    OPENAI_MODEL=gpt-4o
    ```

   Or for Azure OpenAI:

    ```env
    AZURE_OPENAI_ENDPOINT=https://your-azure-resource.openai.azure.com/
    AZURE_OPENAI_DEPLOYMENT=gpt-4-prod
    AZURE_OPENAI_API_KEY=your_azure_api_key
    AZURE_OPENAI_API_VERSION=2023-12-01-preview
    ```

3. **Verify Setup:**
   Ensure everything is set up correctly by running the farm server and exchange as described below.

## Execution

### Step 1: Run the Farm Server
Start the `farm_server`, which acts as an A2A agent, by executing:

```sh
uv run python farm/farm_server.py
```

The `farm_server` listens for requests from the `exchange` and processes them using LangGraph. It generates flavor profiles based on user inputs such as location and season.

### Step 2: Run the Exchange Server
Start the `exchange`, which acts as an A2A client, by running:

```sh
uv run python exchange/main.py
```

Send curl requests to the `exchange` to interact with the `farm_server`. For example, you can send a request to generate a coffee flavor profile:
```sh
curl -X POST http://127.0.0.1:8000/agent/prompt \
-H "Content-Type: application/json" \
-d '{"prompt": "Flavor notes of Ethiopian coffees in the spring"}'
```