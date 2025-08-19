# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
import datetime
import logging
from typing import Any
from pydantic import PrivateAttr

import slim_bindings

from langchain_core.tools import BaseTool
from graph.models import FlavorProfileInput, FlavorProfileOutput

logger = logging.getLogger("corto.supervisor.tools")

class FlavorProfileTool(BaseTool):
    """
    This tool sends a prompt directly to the farm agent via SLIM and returns the flavor profile estimation.
    """
    name: str = "get_flavor_profile"
    description: str = "Estimates the flavor profile of coffee beans based on a given prompt."
    
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)


    def _run(self, input: FlavorProfileInput) -> float:
        raise NotImplementedError("Use _arun for async execution.")

    async def _arun(self, input: FlavorProfileInput, **kwargs: Any) -> float:
        logger.info("FlavorProfileTool has been called.")
        try:
            if not input.get('prompt'):
                logger.error("Invalid input: Prompt must be a non-empty string.")
                raise ValueError("Invalid input: Prompt must be a non-empty string.")
            
            # Create SLIM connection and session
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
                prompt = input.get('prompt')
                logger.info(f"Sending message to receiver: {prompt}")
                
                _, reply = await slim.request_reply(
                    session,
                    prompt.encode(),
                    receiver,
                    timeout=datetime.timedelta(seconds=10)
                )
                response_text = reply.decode()
                logger.info(f"Received response: {response_text}")
                
                return FlavorProfileOutput(flavor_profile=response_text)
        except Exception as e:
            logger.error(f"Failed to get flavor profile: {str(e)}")
            raise RuntimeError(f"Failed to get flavor profile: {str(e)}")