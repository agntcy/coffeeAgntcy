# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
import datetime
import logging
import slim_bindings

logger = logging.getLogger("corto.slim.utils")

# send_receiver function is used to send a message to the SLIM receiver and returns the response.
async def send_receiver(prompt: str) -> str:
    """
    Sends a message to the SLIM receiver and returns the response.
    
    Args:
        prompt (str): The message to send to the receiver
        
    Returns:
        str: The response from the receiver
        
    Raises:
        RuntimeError: If communication with the receiver fails
    """
    logger.info("Connecting to SLIM server for receiver: test.demo.receiver")
    
    # Note: a2a stuff removed for slim v0.4.0 testing, app-sdk dependency removed- transport/bridge removed for a2a to slim
    
    # Create sender and receiver names- hardcoded for now (a2a topic placeholder)
    sender = slim_bindings.PyName("test", "demo", "sender")
    receiver = slim_bindings.PyName("test", "demo", "receiver")
    
    # Create identity provider/verifier with shared secret- hardcoded for now
    provider = slim_bindings.PyIdentityProvider.SharedSecret("test", "secret")
    verifier = slim_bindings.PyIdentityVerifier.SharedSecret("test", "secret")
    
    # Create and connect SLIM
    slim = await slim_bindings.Slim.new(sender, provider, verifier)
    
    try:
        async with slim:
            await slim.connect({"endpoint": "http://localhost:46357", "tls": {"insecure": True}})
            await slim.subscribe(sender)
            
            # Create session and set route
            session = await slim.create_session(slim_bindings.PySessionConfiguration.FireAndForget())
            await slim.set_route(receiver)
            
            # Give receiver time to be ready
            await asyncio.sleep(1)
            
            logger.info("Connected to SLIM server")
            
            # Send message directly
            logger.info(f"Sending message to receiver: {prompt}")
            
            _, reply = await slim.request_reply(
                session,
                prompt.encode(),
                receiver,
                timeout=datetime.timedelta(seconds=10)
            )
            response_text = reply.decode()
            logger.info(f"Received response: {response_text}")
            
            return response_text
    except Exception as e:
        logger.error(f"Failed to send message via SLIM: {e}")
        raise RuntimeError(f"Failed to communicate with receiver: {e}")
