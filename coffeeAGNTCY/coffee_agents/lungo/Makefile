# Makefile for running logistic and farm services with uv
# Each target sets PYTHONPATH to project root before invoking uv

# Variables
PYTHONPATH := $(CURDIR)
UV = PYTHONPATH=$(PYTHONPATH) uv run

# Default target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  logistic-supervisor - Run logistic supervisor"
	@echo "  auction-supervisor  - Run auction supervisor"
	@echo "  shipper             - Run logistic shipper"
	@echo "  accountant          - Run logistic accountant"
	@echo "  logistic-farm       - Run logistic farm service"
	@echo "  brazil-farm         - Run Brazil farm server"
	@echo "  colombia-farm       - Run Colombia farm server"
	@echo "  vietnam-farm        - Run Vietnam farm server"
	@echo "  weather-mcp         - Run weather MCP server"

.PHONY: logistic-supervisor
logistic-supervisor:
	$(UV) agents/supervisors/logistic/main.py

.PHONY: auction-supervisor
auction-supervisor:
	$(UV) agents/supervisors/auction/main.py

.PHONY: shipper
shipper:
	$(UV) agents/logistics/shipper/server.py

.PHONY: accountant
accountant:
	$(UV) agents/logistics/accountant/server.py

.PHONY: logistic-farm
logistic-farm:
	$(UV) agents/logistics/farm/server.py

.PHONY: brazil-farm
brazil-farm:
	$(UV) agents/farms/brazil/farm_server.py

.PHONY: colombia-farm
colombia-farm:
	$(UV) agents/farms/colombia/farm_server.py

.PHONY: vietnam-farm
vietnam-farm:
	$(UV) agents/farms/vietnam/farm_server.py

.PHONY: weather-mcp
weather-mcp:
	$(UV) agents/mcp_servers/weather_service.py