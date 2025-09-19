# Group Conversation Agents Architecture

## Components
- Shipper (`logistic-shipper`): ...
- Accountant (`logistic-accountant`): ...
- Farm (`logistic-farm`): ...
- Supervisor (`logistic-supervisor`): Orchestrates and routes.
- SLIM Gateway (`logistic-slim`): PubSub (56400) + controller (56401).

## Ports
| Purpose | Port | Source |
|---------|------|--------|
| SLIM PubSub | 56400 | `logistic-server-config.yaml` |
| SLIM Controller | 56401 | `logistic-server-config.yaml` |

## Message Flow
1. Supervisor publishes request via SLIM PubSub.
2. Farms consume; unicast vs broadcast determined by routing logic.
3. Responses returned via subscribed channels.
4. Observability exported via OTLP to ClickHouse/Grafana.

## Environment Variables
- `DEFAULT_MESSAGE_TRANSPORT=SLIM`
- `TRANSPORT_SERVER_ENDPOINT=http://logistic-slim:56400`

## Extending
Add a new logistic service:
1. Define container in `docker-compose.logistic.yaml`.
2. Point `TRANSPORT_SERVER_ENDPOINT` to PubSub port.
3. Register any new routing logic in supervisor graph.