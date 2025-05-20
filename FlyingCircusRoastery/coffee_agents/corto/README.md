# Corto Exchange and Farm Server

## Prerequisites

Ensure you have `uv` installed. You can install it using Homebrew:

```sh
brew install uv
```
## Quick Start
**Step 0: Deploy the message bus server**
To run the messaging server (AGP | NATS | MQTT), bring up the services using Docker Compose.
```sh
docker-compose up
```

**Step 1: Run the Farm Server**
Start the farm server by executing the following command:
```sh
uv run farm/farm_server.py
```

**Step 2: Run the Exchange Server**
To start the exchange server, set the PYTHONPATH environment variable and run the server:
```
uv run exchange/main.py
```