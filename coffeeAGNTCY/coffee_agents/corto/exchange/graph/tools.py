# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any

from langchain_core.tools import BaseTool
from graph.models import FlavorProfileInput, FlavorProfileOutput
from graph.slim_utils import send_receiver

logger = logging.getLogger("corto.supervisor.tools")

class FlavorProfileTool(BaseTool):
    """
    This tool sends a prompt directly to the farm agent via SLIM and returns the flavor profile estimation. Use the send_receiver function to send the prompt to the farm agent.
    
    Args:
        input (FlavorProfileInput): The input to the tool.
    
    Returns:
        FlavorProfileOutput: The output of the tool.
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
            
            prompt = input.get('prompt')
            # send the prompt to the farm agent via SLIM
            response_text = await send_receiver(prompt)
            
            return FlavorProfileOutput(flavor_profile=response_text)
        except Exception as e:
            logger.error(f"Failed to get flavor profile: {str(e)}")
            raise RuntimeError(f"Failed to get flavor profile: {str(e)}")