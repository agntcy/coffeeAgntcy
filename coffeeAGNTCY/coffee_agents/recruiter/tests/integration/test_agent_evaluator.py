# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Docker-only integration tests for the agent_evaluator sample agent."""

import pytest


class TestSampleAgentIntegration:
    """Integration tests using the sample A2A agent."""

    @pytest.mark.asyncio
    async def test_sample_agent_starts_and_responds(self, run_sample_a2a_agent):
        """Test that the sample agent starts and responds to requests."""
        import httpx

        process, url = run_sample_a2a_agent()

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{url}/.well-known/agent.json")
            assert response.status_code == 200

            card = response.json()
            assert card["name"] == "TestAgent"
            assert card["version"] == "1.0.0"
