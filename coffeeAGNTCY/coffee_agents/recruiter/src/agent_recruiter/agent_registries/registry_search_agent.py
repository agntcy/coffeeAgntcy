# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
ADK-based agent for searching agent registries via MCP.

This agent uses Google ADK with McpToolset to automatically 
discover and use tools from the Directory MCP server. It can
search for agents based on user queries and manage schema 
transformations.
"""

import os
import subprocess
from typing import Optional, Any

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
from dotenv import load_dotenv
from agent_recruiter.common.logging import get_logger

load_dotenv()  # Load environment variables from .env file

LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o")

logger = get_logger(__name__)


# ============================================================================
# State-Writing Tool for Agent Records
# ============================================================================

async def store_search_results(
    cid: str,
    record: dict[str, Any],
    tool_context: ToolContext
) -> dict[str, Any]:
    """Store an agent record in session state for other agents to access.

    Call this tool after searching for agents or exporting/translating records
    to persist them in session state. This allows other agents in the team
    to access the found agent records.

    Args:
        cid: The Content ID (CID) of the agent record, used as the key
        record: The raw JSON record from search or export/translation
        tool_context: ADK tool context for state access (automatically injected)

    Returns:
        Confirmation with storage status
    """
    # Get existing records dict or initialize empty
    existing: dict[str, Any] = tool_context.state.get("found_agent_records", {})

    # Check if this is an update or new record
    is_update = cid in existing

    # Store/update the record keyed by CID
    existing[cid] = record
    tool_context.state["found_agent_records"] = existing

    action = "Updated" if is_update else "Stored"
    logger.info(f"{action} agent record with CID '{cid}' in session state (total records: {len(existing)})")

    return {
        "status": "success",
        "action": "updated" if is_update else "stored",
        "cid": cid,
        "total_records": len(existing)
    }


# Create the tool wrapper for the store function
store_search_results_tool = FunctionTool(func=store_search_results)


AGENT_INSTRUCTION = """You are an agent registry search assistant. Your job is to SEARCH for agents in the AGNTCY Directory Service.

You have access to MCP tools from the Directory server that let you:
- Search for agents with filters (names, skills, modules, etc.)
- Pull agent records by CID
- Export records from OASF to A2A

You also have a special tool for state management:
- store_search_results: Stores agent records in session state so other agents can access them

Search supports wildcard patterns:
- * matches any sequence of characters
- ? matches any single character
- [abc] matches any character in the set

When searching:
1. First understand what the user is looking for
2. Use the search tool with appropriate filters
3. Pull full records for promising matches
4. IMPORTANT: If the record contains an a2a module, first export it from OASF to A2A using the export tool
5. IMPORTANT: Call store_search_results with the CID and record to persist in session state
6. Return a structured summary of findings (see format below)

IMPORTANT - Your final response MUST include a clear summary in this format:
---
**Found [N] agent(s):**

1. **[Agent Name]** (CID: [cid])
   - Description: [brief description]
   - Skills: [list of skills if available]
   - Protocol: [A2A/MCP if known]

[Repeat for each agent found]

Would you like to search for more agents or evaluate any of these agents?
---

If no agents were found, clearly state that no matching agents were found.
"""


def _check_container_running(container_name: str) -> bool:
    """
    Check if a Docker container is running.
    
    Args:
        container_name: Name or ID of the container to check.
        
    Returns:
        True if container is running, False otherwise.
    """
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            logger.warning(f"Docker command failed: {result.stderr}")
            return False
            
        running_containers = result.stdout.strip().split('\n')
        is_running = container_name in running_containers
        
        if is_running:
            logger.info(f"Container '{container_name}' is running")
        else:
            logger.warning(f"Container '{container_name}' is not running")
            
        return is_running
        
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout checking container '{container_name}' status")
        return False
    except FileNotFoundError:
        logger.error("Docker command not found. Ensure Docker is installed and in PATH")
        return False
    except Exception as e:
        logger.error(f"Error checking container '{container_name}' status: {e}")
        return False


def create_mcp_toolset(
    mcp_container_name: str = "dir-mcp-server",
    tool_filter: Optional[list[str]] = None,
) -> McpToolset:
    """
    Create an McpToolset for the Agntcy Directory MCP server.

    Args:
        mcp_container_name: Docker container name running the MCP server.
        tool_filter: Optional list of tool names to expose (default: all tools).

    Returns:
        Configured McpToolset.
        
    Raises:
        RuntimeError: If Docker is not available or container is not running.
        ConnectionError: If unable to connect to the MCP server.
    """
    # First check if the container is running
    if not _check_container_running(mcp_container_name):
        error_msg = f"Container '{mcp_container_name}' is not running"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    try:
        toolset = McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="docker",
                    args=["exec", "-i", mcp_container_name, "./dirctl", "mcp", "serve"],
                ),
            ),
            tool_filter=tool_filter,
        )
        logger.info(f"Successfully created MCP toolset for container: {mcp_container_name}")
        return toolset
    except Exception as e:
        error_msg = f"Failed to create MCP toolset for container '{mcp_container_name}': {e}"
        logger.error(error_msg)
        logger.error("Ensure the container has the './dirctl mcp serve' command available")
        raise RuntimeError(error_msg) from e


def create_registry_search_agent(
    mcp_container_name: str = "dir-mcp-server",
    tool_filter: Optional[list[str]] = None,
) -> Agent:
    """
    Create an ADK agent for searching agent registries via MCP.

    This is the synchronous factory function for creating the agent,
    compatible with ADK web server and cloud deployments.

    Args:
        mcp_container_name: Docker container name running the MCP server.
        tool_filter: Optional list of tool names to expose (default: all tools).
        
    Note:
        Model configuration is read from environment variables via llm.py:
        - LLM_MODEL: Model identifier (default: "openai/gpt-4o")
        - LITELLM_PROXY_BASE_URL: Optional proxy URL
        - LITELLM_PROXY_API_KEY: Optional proxy API key

    Returns:
        Configured Agent with MCP toolset.
    """
    try:
        # Create MCP toolset with error handling
        mcp_toolset = create_mcp_toolset(mcp_container_name, tool_filter)

        try:
            agent = Agent(
                model=LiteLlm(model=LLM_MODEL),
                name="registry_search_agent",
                instruction=AGENT_INSTRUCTION,
                description="Agent for searching, retrieving, and exporting agent records from the AGNTCY Directory",
                tools=[mcp_toolset, store_search_results_tool],
            )
            return agent
        except Exception as e:
            error_msg = f"Failed to create Agent: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
            
    except Exception as e:
        logger.error(f"Failed to create registry search agent: {e}")
        raise