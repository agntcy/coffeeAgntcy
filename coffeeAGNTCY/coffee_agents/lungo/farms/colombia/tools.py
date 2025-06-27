from contextlib import AsyncExitStack
from typing import Optional

from langchain_core.tools import tool
from langchain.tools import StructuredTool
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
import httpx

class MCPClient:
    """
    A client for connecting to an MCP server using HTTP Streamable transport.
    This class manages the connection and provides a session for making requests.
    """

    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

    async def connect(
            self, server_url: str, headers: Optional[dict] = None
        ):
            """Connect to an MCP server running with HTTP Streamable transport"""
            self._streams_context = streamablehttp_client(
            url=server_url,
            headers=headers or {},
        )
            read_stream, write_stream, _ = await self._streams_context.__aenter__()
            self._session_context = ClientSession(read_stream, write_stream)
            self.session = await self._session_context.__aenter__() 

            await self.session.initialize()
            print("Connected to MCP server")

    async def cleanup(self):
        """Properly clean up the session and streams"""
        if self._session_context:
            await self._session_context.__aexit__(None, None, None)
        if self._streams_context:  # pylint: disable=W0125
            await self._streams_context.__aexit__(None, None, None)
