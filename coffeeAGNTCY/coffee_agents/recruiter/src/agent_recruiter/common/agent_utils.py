# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from google.genai import types

async def call_agent_async(query: str, runner, user_id: str, session_id: str) -> str:
    """Sends a query to an agent and returns the final response."""
    content = types.Content(role='user', parts=[types.Part(text=query)])

    final_response_text = "Agent did not produce a final response."

    async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
            break

    return final_response_text