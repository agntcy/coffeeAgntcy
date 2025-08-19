# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
import slim_bindings
from dotenv import load_dotenv

from agent import FarmAgent

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
    
    # Note: a2a stuff removed for slim v0.4.0 testing, app-sdk dependency removed- transport/bridge removed for a2a to slim
    
    # Create SLIM receiver- hardcoded receiver name(a2a topic placeholder)
    receiver = slim_bindings.PyName("test", "demo", "receiver")
    #hardcodeed shared secret
    provider = slim_bindings.PyIdentityProvider.SharedSecret("test", "secret")
    verifier = slim_bindings.PyIdentityVerifier.SharedSecret("test", "secret")
    
    slim = await slim_bindings.Slim.new(receiver, provider, verifier)
    
    async with slim:
        await slim.connect({"endpoint": "http://localhost:46357", "tls": {"insecure": True}})
        await slim.subscribe(receiver)
        logger.info("Farm agent SLIM receiver started...")
        
        while True:
            session_info, _ = await slim.receive()
            
            async def handle_session(session_id):
                while True:
                    try:
                        session, msg = await slim.receive(session=session_id)
                        text = msg.decode()
                        logger.info(f"Received message: {text}")
                        
                        # Use farm agent to process the message
                        result = await farm_agent.ainvoke(text)
                        response = result.get("flavor_notes", "Error processing request")
                        
                        await slim.publish_to(session, response.encode())
                        logger.info(f"Processed '{text}' -> Generated response: {response}")
                    except Exception as e:
                        logger.error(f"Session {session_id} error: {e}")
                        break
            
            asyncio.create_task(handle_session(session_info.id))

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully on keyboard interrupt.")
    except Exception as e:
        logger.error(f"Error occurred: {e}")
