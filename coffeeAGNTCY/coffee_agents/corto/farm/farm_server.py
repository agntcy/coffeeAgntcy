# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
from dotenv import load_dotenv

from agent import FarmAgent
from slim_receiver_utils import start_slim_receiver

load_dotenv()

# Setup logging
logger = logging.getLogger("corto.farm.server")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

async def main():
    """
    Starts the farm agent server using direct SLIM communication.
    Receives messages via SLIM and processes them using FarmAgent.
    """
    
    # Initialize the farm agent
    farm_agent = FarmAgent()
    
    # Start SLIM receiver with farm agent as message processor
    await start_slim_receiver(farm_agent.ainvoke)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully on keyboard interrupt.")
    except Exception as e:
        logger.error(f"Error occurred: {e}")
