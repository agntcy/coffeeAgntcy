#!/usr/bin/env python3
"""Cross-Node Pull Test - MCP Server"""

import asyncio
import json
import time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_crossnode_pull():
    print("=" * 50)
    print("MCP SERVER - CROSS-NODE PULL TEST")
    print("Push → Publish → Search → Pull (no sync)")
    print("=" * 50)
    
    # Create record matching the working SDK test
    record_data = {
        "schema_version": "0.8.0",
        "name": f"mcp-crossnode-test-{int(time.time())}",
        "version": "v1.0.0",
        "description": "MCP cross-node test",
        "authors": ["Test"],
        "created_at": "2026-03-03T00:00:00Z",
        "skills": [{"name": "natural_language_processing/natural_language_generation/text_completion", "id": 10201}],
        "locators": [{"type": "docker_image", "url": "https://example.com/test"}],
        "domains": [{"name": "technology/networking", "id": 103}]
    }
    
    # Server params for Node 1
    server_params_1 = StdioServerParameters(
        command="python",
        args=["server.py"],
        env={
            "DIRECTORY_SERVER_ADDRESS": "sn-dir1.labs.outshift.com:8888",
            "SPIFFE_SOCKET_PATH": "/run/spire/sockets/agent.sock",
            "AUTH_MODE": "x509"
        }
    )
    
    # Server params for Node 2
    server_params_2 = StdioServerParameters(
        command="python",
        args=["server.py"],
        env={
            "DIRECTORY_SERVER_ADDRESS": "sn-dir2.labs.outshift.com:8888",
            "SPIFFE_SOCKET_PATH": "/run/spire/sockets/agent.sock",
            "AUTH_MODE": "x509"
        }
    )
    
    # 1. Push on Node 1
    print("\n1️⃣  PUSH record on Node 1")
    async with stdio_client(server_params_1) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            push_result = await session.call_tool("push", {"record": record_data})
            result_data = json.loads(push_result.content[0].text)
            cid = result_data["cid"]
            print(f"   ✅ CID: {cid}")
    
    # 2. Publish on Node 1
    print("\n2️⃣  PUBLISH on Node 1")
    async with stdio_client(server_params_1) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            publish_result = await session.call_tool("routing_publish", {"cid": cid})
            print("   ✅ Published")
    
    # 3. Wait for propagation with progressive search
    print("\n3️⃣  Wait for publication to propagate (up to 2 minutes)")
    
    found = False
    peer_addr = None
    total_wait = 0
    
    for wait in [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10]:
        await asyncio.sleep(wait)
        total_wait += wait
        
        async with stdio_client(server_params_2) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                search_result = await session.call_tool("routing_search", {
                    "skill": "natural_language_processing",
                    "limit": 50
                })
                search_data = json.loads(search_result.content[0].text)
                
                for result in search_data.get("results", []):
                    if result.get("record_ref", {}).get("cid") == cid:
                        peer_addr = result.get("peer", {}).get("addrs", [None])[0]
                        found = True
                        print(f"   ✅ Found after {total_wait}s")
                        break
        
        if found:
            break
        print(f"   ⏳ Waiting... ({total_wait}s elapsed)")
    
    # 4. Verify found
    print("\n4️⃣  SEARCH from Node 2")
    if not found:
        print("   ❌ Record not found after 2 minutes")
        return False
    
    print(f"   ✅ Found CID: {cid}")
    print(f"   📍 Peer Address: {peer_addr}")
    
    # 5. Pull from peer address (cross-node, no sync)
    print("\n5️⃣  PULL from peer address (cross-node, no sync required)")
    
    server_params_peer = StdioServerParameters(
        command="python",
        args=["server.py"],
        env={
            "DIRECTORY_SERVER_ADDRESS": peer_addr,
            "SPIFFE_SOCKET_PATH": "/run/spire/sockets/agent.sock",
            "AUTH_MODE": "x509"
        }
    )
    
    async with stdio_client(server_params_peer) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            pull_result = await session.call_tool("pull", {"cid": cid})
            pull_data = json.loads(pull_result.content[0].text)
            print(f"   ✅ Pulled from {peer_addr}: {pull_data.get('name', 'Unknown')}")
    
    print("\n" + "=" * 50)
    print("✅ CROSS-NODE PULL TEST PASSED!")
    print("=" * 50)
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(test_crossnode_pull())
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
