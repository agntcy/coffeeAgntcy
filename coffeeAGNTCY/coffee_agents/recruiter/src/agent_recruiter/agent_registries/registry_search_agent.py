# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
ADK-based agent for searching agent registries via the AGNTCY Directory.

Searches run a single tool (`search_agents`) that drives the local `dirctl`
binary directly: one batch `dirctl export` searches, transforms each match to
its A2A AgentCard, and writes them out, which we then persist to session state.
A small MCP toolset is also attached, filtered down to the OASF schema-discovery
tools so the agent can resolve valid skill/domain names before filtering on them.
"""

import asyncio
import json
import os
import shutil
import tempfile
from pathlib import Path
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

# Timeout for MCP server startup (in seconds) - increase if you see startup timeouts
MCP_SERVER_STARTUP_TIMEOUT = int(os.getenv("MCP_SERVER_STARTUP_TIMEOUT", "30"))

# Read-only OASF schema tools exposed for skill/domain discovery. The atomic
# search/pull/export MCP tools are intentionally excluded — `search_agents`
# replaces them with a single bulk call.
DISCOVERY_TOOLS = [
    "agntcy_oasf_get_schema_skills",
    "agntcy_oasf_get_schema_domains",
    "agntcy_oasf_list_versions",
]

logger = get_logger(__name__)


def _dirctl_path() -> str:
    """Return the dirctl binary path, raising if it is not on PATH."""
    path = shutil.which("dirctl")
    if not path:
        raise RuntimeError("dirctl binary not found in PATH. Install dirctl to use the directory.")
    return path


def _dirctl_env() -> dict[str, str]:
    """Directory client settings passed to every dirctl invocation."""
    return {
        "DIRECTORY_CLIENT_SERVER_ADDRESS": os.getenv("DIRECTORY_CLIENT_SERVER_ADDRESS", "localhost:8888"),
        "DIRECTORY_CLIENT_TLS_SKIP_VERIFY": os.getenv("DIRECTORY_CLIENT_TLS_SKIP_VERIFY", "true"),
        "OASF_API_VALIDATION_SCHEMA_URL": os.getenv("OASF_API_VALIDATION_SCHEMA_URL", "https://schema.oasf.outshift.com"),
    }


def create_discovery_mcp_toolset(
    tool_filter: Optional[list[str]] = None,
) -> McpToolset:
    """Create an McpToolset exposing the OASF schema-discovery tools.

    Args:
        tool_filter: Tool names to expose (default: ``DISCOVERY_TOOLS``).

    Raises:
        RuntimeError: If the toolset cannot be created.
    """
    dirctl_path = _dirctl_path()
    try:
        toolset = McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=dirctl_path,
                    args=["mcp", "serve"],
                    env=_dirctl_env(),
                ),
                timeout=MCP_SERVER_STARTUP_TIMEOUT,
            ),
            tool_filter=tool_filter if tool_filter is not None else DISCOVERY_TOOLS,
        )
        logger.info(f"Created discovery MCP toolset (dirctl at {dirctl_path})")
        return toolset
    except Exception as e:
        error_msg = f"Failed to create discovery MCP toolset: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


# ============================================================================
# Search + Export + Persist — single deterministic tool
# ============================================================================


async def _run_dirctl(args: list[str], timeout: float = 30.0) -> str:
    """Run a dirctl command and return its stdout.

    Args:
        args: dirctl subcommand and flags (e.g. ``["search", "--name", "web*"]``).
        timeout: Seconds to wait before killing the process.

    Raises:
        RuntimeError: If dirctl exits non-zero or times out.
    """
    env = _dirctl_env()
    global_flags: list[str] = []
    if env["DIRECTORY_CLIENT_TLS_SKIP_VERIFY"].strip().lower() in ("1", "true", "yes"):
        global_flags.append("--tls-skip-verify")

    proc = await asyncio.create_subprocess_exec(
        _dirctl_path(), *args, *global_flags,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={**os.environ, **env},
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError as e:
        proc.kill()
        await proc.wait()
        raise RuntimeError(f"dirctl {' '.join(args)} timed out after {timeout}s") from e

    if proc.returncode != 0:
        raise RuntimeError(
            f"dirctl {' '.join(args)} failed (exit {proc.returncode}): {stderr.decode().strip()}"
        )
    return stdout.decode()


# Batch a2a export fails on any record lacking an A2A module, so we restrict to
# A2A-capable records by default. This also satisfies dirctl's "≥1 filter" rule.
_A2A_MODULE = "integration/a2a"


async def search_agents(
    tool_context: ToolContext,
    name: Optional[list[str]] = None,
    skill: Optional[list[str]] = None,
    module: Optional[list[str]] = None,
    version: Optional[list[str]] = None,
    domain: Optional[list[str]] = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Search the AGNTCY Directory and persist every match as an A2A card.

    Queries the directory with the given filters, exports each match to its A2A
    AgentCard, and stores them all in session state under ``found_agent_records``
    (keyed by CID) for other agents to consume.

    Pass only the filters implied by the request (no filters matches every
    agent). All filters accept wildcards: ``*`` (any sequence), ``?`` (single
    char), ``[abc]`` (any char in the set).

    Args:
        tool_context: ADK tool context for state access (auto-injected).
        name: Agent name patterns (e.g. ``["web*", "*-agent"]``).
        skill: Skill names (e.g. ``["natural_language_processing"]``).
        module: Module names (defaults to ``["integration/a2a"]`` when omitted,
            since results are exported as A2A cards).
        version: Version patterns or comparisons (e.g. ``["v1.*"]``, ``[">=1.0.0"]``).
        domain: Domain patterns (e.g. ``["*education*"]``).
        limit: Maximum number of records to return (default 20).

    Returns:
        Summary dict: ``status``, ``count``, ``agents`` (id/name/description/
        skills), and ``total_records`` now in session state.
    """
    filters: list[str] = []
    for flag, values in (
        ("--name", name),
        ("--skill", skill),
        ("--module", module),
        ("--version", version),
        ("--domain", domain),
    ):
        # The LLM may pass a bare string; wrap it so we don't iterate characters.
        if isinstance(values, str):
            values = [values]
        for value in values or []:
            filters.extend([flag, value])
    # Restrict to A2A-capable records unless the caller named a specific module.
    if not module:
        filters.extend(["--module", _A2A_MODULE])

    # One batch export: search + OASF->A2A transform + write, for every match.
    records: dict[str, Any] = tool_context.state.get("found_agent_records", {})
    found: list[dict[str, Any]] = []
    export_dir = tempfile.mkdtemp(prefix="agntcy_a2a_")
    try:
        await _run_dirctl(
            ["export", "--output-dir", export_dir, "--format", "a2a", *filters, "--limit", str(limit)]
        )
        for path in sorted(Path(export_dir).glob("*.json")):
            try:
                card = json.loads(path.read_text())
            except (OSError, json.JSONDecodeError) as e:
                logger.warning(f"Skipping unreadable A2A card '{path.name}': {e}")
                continue
            key = path.stem  # dirctl names files by agent (latest version per name)
            records[key] = card
            found.append(
                {
                    "id": key,
                    "name": card.get("name", "Unknown"),
                    "description": card.get("description", ""),
                    "skills": [s.get("name") for s in card.get("skills") or [] if isinstance(s, dict)],
                }
            )
    finally:
        shutil.rmtree(export_dir, ignore_errors=True)

    if not found:
        logger.info(f"Search returned no matching agents (filters={filters})")
        return {
            "status": "success",
            "count": 0,
            "agents": [],
            "message": "No matching agents were found.",
        }

    tool_context.state["found_agent_records"] = records
    logger.info(f"Stored {len(found)} agent record(s) in session state in one batch (total: {len(records)})")

    return {
        "status": "success",
        "count": len(found),
        "agents": found,
        "total_records": len(records),
    }


# Create the tool wrapper for the search function
search_agents_tool = FunctionTool(func=search_agents)


AGENT_INSTRUCTION = """You are an agent registry search assistant for the AGNTCY Directory Service.

For ANY request to find or search for agents:
1. If the request references a skill or domain, you may call the discovery tools
   (agntcy_oasf_get_schema_skills / agntcy_oasf_get_schema_domains) to confirm
   the exact name. Skill and domain names are full hierarchical paths of the
   form "parent/child" (e.g. "agent_orchestration/agent_coordination") — always
   use the COMPLETE name, never just the parent or just the child. Do this ONCE.
2. Call `search_agents` EXACTLY ONCE with filters from the request, passing each
   value VERBATIM (do not split or shorten it). It searches, exports each match
   to its A2A card, and persists everything in one step.
   Filters (pass only those implied by the request; all accept wildcards
   * ? [abc]):
   - name: agent name patterns
   - skill: full skill paths ("parent/child")
   - module: module names (e.g. integration/a2a)
   - version: version patterns or comparisons (e.g. v1.*, >=1.0.0)
   - domain: full domain names
   - limit: max results (default 20)
   Do NOT ask for clarification — just search with what you have.
3. Summarize the results returned by `search_agents` in the format below.

**Your final response MUST include a clear summary in this format:**
---
**Found [N] agent(s):**

1. **[Agent Name]**
   - Description: [brief description]
   - Skills: [list of skills if available]

[Repeat for each agent found]
---

If no agents were found, clearly state that no matching agents were found.
"""


def create_registry_search_agent(
    tool_filter: Optional[list[str]] = None,
) -> Agent:
    """Create an ADK agent for searching agent registries.

    Synchronous factory compatible with the ADK web server and cloud
    deployments. Model configuration is read from environment variables.

    Args:
        tool_filter: Optional override for the discovery MCP tools to expose
            (default: ``DISCOVERY_TOOLS``).

    Returns:
        Configured Agent with the `search_agents` tool and the discovery toolset.
    """
    try:
        discovery_toolset = create_discovery_mcp_toolset(tool_filter)
        return Agent(
            model=LiteLlm(model=LLM_MODEL, temperature=0.1),
            name="registry_search_agent",
            instruction=AGENT_INSTRUCTION,
            description="Agent for searching and retrieving agent records from the AGNTCY Directory",
            tools=[search_agents_tool, discovery_toolset],
        )
    except Exception as e:
        logger.error(f"Failed to create registry search agent: {e}")
        raise
