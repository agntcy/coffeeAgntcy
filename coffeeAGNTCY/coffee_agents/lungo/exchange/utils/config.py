import os

# Used for Agntcy Identity integration
brazil_farm_url = os.getenv("BRAZIL_FARM_AGENT_URL", "http://0.0.0.0:9999")
columbia_farm_url = os.getenv("COLOMBIA_FARM_AGENT_URL", "http://0.0.0.0:9998")
vietnam_farm_url = os.getenv("VIETNAM_FARM_AGENT_URL", "http://0.0.0.0:9997")