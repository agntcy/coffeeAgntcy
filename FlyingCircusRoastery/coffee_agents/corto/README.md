# Corto Exchange and Farm Server

## Prerequisites

Ensure you have `uv` installed. You can install it using Homebrew:

```sh
brew install uv
```
## Quick Start
**Step 1: Run the Farm Server**
Start the farm server by executing the following command:
```sh
uv run farm/farm_server.py
```

**Step 2: Run the Exchange Server**
To start the exchange server, set the PYTHONPATH environment variable and run the server:
```
export PYTHONPATH=$(pwd)/exchange && uv run exchange/main.py
```

**Step 2.1: Run the Streamlit App**  
As a prerequisite, ensure you have the `streamlit` package installed. You can install it using pip:
```sh
uv pip install streamlit
```
Then, run the following command to start the Streamlit app:
```
To start the Streamlit interface for the exchange server, navigate to the `exchange` directory and run the following command:
```sh
streamlit run exchange/ui/exchange_streamlit.py
```