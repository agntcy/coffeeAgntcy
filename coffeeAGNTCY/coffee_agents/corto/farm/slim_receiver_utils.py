# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
import slim_bindings
from typing import Callable, Any, Awaitable

logger = logging.getLogger("corto.farm.slim.receiver")

async def start_slim_receiver(message_processor: Callable[[str], Awaitable[Any]]) -> None:
    """
    Starts a SLIM receiver that processes incoming messages and sends responses back to sender.
    
    Args:
        message_processor: Async callable that takes a message string and returns a response dict
                          Expected to return dict with structure like {"flavor_notes": "response"}
    """
    logger.info("Setting up SLIM receiver...")
    
    # Note: a2a stuff removed for slim v0.4.0 testing, app-sdk dependency removed- transport/bridge removed for a2a to slim
    
    # Create SLIM receiver- hardcoded receiver name(a2a topic placeholder)
    receiver = slim_bindings.PyName("test", "demo", "receiver")
    # hardcoded shared secret
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
                        
                        # Process message using the provided processor
                        result = await message_processor(text)
                        response = result.get("flavor_notes", "Error processing request")
                        
                        # Send response back to sender
                        await slim.publish_to(session, response.encode())
                        logger.info(f"Processed '{text}' -> Generated response: {response}")
                    except Exception as e:
                        logger.error(f"Session {session_id} error: {e}")
                        break
            
            asyncio.create_task(handle_session(session_info.id))
