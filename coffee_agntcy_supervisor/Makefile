venv/bin/activate:
	@echo "Setting up virtual environment..."
	@if [ ! -d "venv" ]; then \
		python3 -m venv venv; \
	fi
	@echo "Activating virtual environment and installing requirements..."
	. venv/bin/activate

run: venv/bin/activate
	@echo "Running the application with Uvicorn reload on port 8125..."
	. venv/bin/activate && poetry install && export PYTHONPATH=${PYTHONPATH}:$(ROOT_DIR)/supervisor && python3 supervisor/main.py

run-server: venv/bin/activate
	@echo "Running the application with Uvicorn reload on port 8125..."
	. venv/bin/activate && poetry install && export PYTHONPATH=${PYTHONPATH}:$(ROOT_DIR)/supervisor && python3 supervisor/main.py --server