#!/usr/bin/env python3
"""
Test the Directory MCP Server with remote directory nodes using SPIFFE authentication
"""

import asyncio
import json
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_remote_directories():
    """Test the directory MCP server with remote nodes"""
    
    # Test both directory nodes
    nodes = [
        "sn-dir1.labs.outshift.com:8888",
        "sn-dir2.labs.outshift.com:8888"
    ]
    
    for node in nodes:
        print(f"\n{'='*60}")
        print(f"Testing with node: {node}")
        print(f"{'='*60}\n")
        
        # Server parameters with SPIFFE authentication
        server_params = StdioServerParameters(
            command="python",
            args=["server.py"],
            env={
                "DIRECTORY_SERVER_ADDRESS": node,
                "SPIFFE_SOCKET_PATH": "/run/spire/sockets/agent.sock",
                "AUTH_MODE": "x509"
            }
        )
        
        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize the session
                    await session.initialize()
                    print(f"✅ Connected to {node}\n")
                    
                    # Test 1: Search for agents
                    print("🔍 Test 1: Search for all agents...")
                    try:
                        search_result = await session.call_tool(
                            "search",
                            arguments={"name": "*"}
                        )
                        for content in search_result.content:
                            if hasattr(content, 'text'):
                                data = json.loads(content.text)
                                count = data.get('count', 0)
                                print(f"  ✅ Found {count} agents")
                                if data.get('results'):
                                    for i, result in enumerate(data['results'][:5], 1):
                                        print(f"    {i}. {result.get('name', 'Unknown')}")
                                    if count > 5:
                                        print(f"    ... and {count - 5} more")
                    except Exception as e:
                        print(f"  ❌ Search failed: {e}")
                    
                    print()
                    
                    # Test 2: Search by skill
                    print("🔍 Test 2: Search by skill...")
                    try:
                        search_result = await session.call_tool(
                            "search",
                            arguments={"skill": "AI"}
                        )
                        for content in search_result.content:
                            if hasattr(content, 'text'):
                                data = json.loads(content.text)
                                count = data.get('count', 0)
                                print(f"  ✅ Found {count} agents with 'AI' skill")
                    except Exception as e:
                        print(f"  ❌ Search failed: {e}")
                    
                    print()
                    
        except Exception as e:
            print(f"❌ Failed to connect to {node}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("✅ Remote directory tests completed!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    try:
        asyncio.run(test_remote_directories())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
