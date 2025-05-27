import os
from dotenv import load_dotenv

load_dotenv()  # Automatically loads from `.env` or `.env.local`

# --- Corto ---
FARM_AGENT_HOST = os.getenv("FARM_AGENT_HOST", "localhost")
FARM_AGENT_PORT = int(os.getenv("FARM_AGENT_PORT", "9999"))

LLM_PROVIDER = os.getenv("LLM_PROVIDER")
