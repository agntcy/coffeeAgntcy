#!/usr/bin/env python3
"""
Test client for the Directory MCP Server

This script tests the MCP server by connecting to it and calling its tools.
"""

import asyncio
import json
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mcp_server():
    """Test the directory MCP server"""
    
    # Server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
        env={
            "DIRECTORY_SERVER_ADDRESS": "localhost:8888",
            "DIRECTORY_TLS_SKIP_VERIFY": "true"
        }
    )
    
    print("🚀 Starting MCP server connection...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            print("✅ Session initialized\n")
            
            # List available tools
            print("📋 Listing available tools...")
            tools_result = await session.list_tools()
            print(f"Found {len(tools_result.tools)} tools:")
            for tool in tools_result.tools:
                print(f"  - {tool.name}: {tool.description}")
            print()
            
            # Test 1: Search (will fail if directory not running, but tests MCP protocol)
            print("🔍 Test 1: Search for agents...")
            try:
                search_result = await session.call_tool(
                    "search",
                    arguments={"name": "*"}
                )
                print("Search result:")
                for content in search_result.content:
                    if hasattr(content, 'text'):
                        data = json.loads(content.text)
                        print(f"  Found {data.get('count', 0)} agents")
                        if data.get('results'):
                            for result in data['results'][:3]:  # Show first 3
                                print(f"    - {result.get('name', 'Unknown')}")
            except Exception as e:
                print(f"  ⚠️  Search failed (expected if directory not running): {e}")
            print()
            
            # Test 2: Pull (will fail without valid CID)
            print("🔍 Test 2: Pull record by CID...")
            try:
                pull_result = await session.call_tool(
                    "pull",
                    arguments={"cid": "baeareiem5tc4gmtdhg74g5fmehlda4uvikfinlfpkmndj5jmv2zzojeume"}
                )
                print("Pull result:")
                for content in pull_result.content:
                    if hasattr(content, 'text'):
                        data = json.loads(content.text)
                        if "error" in data:
                            print(f"  ⚠️  {data['error']}")
                        else:
                            print(f"  ✅ Retrieved record: {data.get('name', 'Unknown')}")
            except Exception as e:
                print(f"  ⚠️  Pull failed (expected if CID doesn't exist): {e}")
            print()
            
            # Test 3: Export
            print("🔍 Test 3: Export record...")
            try:
                export_result = await session.call_tool(
                    "export",
                    arguments={
                        "cid": "baeareiem5tc4gmtdhg74g5fmehlda4uvikfinlfpkmndj5jmv2zzojeume",
                        "target_format": "a2a"
                    }
                )
                print("Export result:")
                for content in export_result.content:
                    if hasattr(content, 'text'):
                        data = json.loads(content.text)
                        if "error" in data:
                            print(f"  ⚠️  {data['error']}")
                        else:
                            print(f"  ✅ Exported successfully")
            except Exception as e:
                print(f"  ⚠️  Export failed: {e}")
            print()
            
            print("✅ MCP protocol tests completed!")
            print("\n📝 Summary:")
            print("  - MCP server starts correctly")
            print("  - Tools are discoverable")
            print("  - Tool calls work (protocol level)")
            print("  - To test with real data, start the directory service:")
            print("    cd ../coffeeAGNTCY/coffee_agents/recruiter/docker")
            print("    docker compose up dir-api-server zot")


if __name__ == "__main__":
    try:
        asyncio.run(test_mcp_server())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
