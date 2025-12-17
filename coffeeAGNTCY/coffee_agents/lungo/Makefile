# Makefile for running logistics and farm services with uv
# Each target sets PYTHONPATH to project root before invoking uv

# Variables
PYTHONPATH := $(CURDIR)
UV = PYTHONPATH=$(PYTHONPATH) uv run

# Default target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  logistics-supervisor - Run logistics supervisor"
	@echo "  auction-supervisor  - Run auction supervisor"
	@echo "  shipper             - Run logistics shipper"
	@echo "  accountant          - Run logistics accountant"
	@echo "  logistics-farm       - Run logistics farm service"
	@echo "  brazil-farm         - Run Brazil farm server"
	@echo "  colombia-farm       - Run Colombia farm server"
	@echo "  vietnam-farm        - Run Vietnam farm server"
	@echo "  weather-mcp         - Run weather MCP server"
	@echo "  payment-mcp         - Run payment MCP server"
	@echo "  helpdesk            - Run logistics helpdesk"

.PHONY: logistics-supervisor
logistics-supervisor:
	$(UV) agents/supervisors/logistics/main.py

.PHONY: auction-supervisor
auction-supervisor:
	$(UV) agents/supervisors/auction/main.py

.PHONY: shipper
shipper:
	$(UV) agents/logistics/shipper/server.py

.PHONY: accountant
accountant:
	$(UV) agents/logistics/accountant/server.py

.PHONY: logistics-farm
logistics-farm:
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

.PHONY: payment-mcp
payment-mcp:
	$(UV) agents/mcp_servers/payment_service.py

.PHONY: helpdesk
helpdesk:
	$(UV) agents/logistics/helpdesk/server.py
