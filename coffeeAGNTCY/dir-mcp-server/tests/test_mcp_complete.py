#!/usr/bin/env python3
"""Complete Federation Test - MCP Server"""

import asyncio
import json
import time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_complete_federation():
    print("=" * 50)
    print("MCP SERVER COMPLETE FEDERATION TEST")
    print("=" * 50)
    
    # Create record matching the working SDK test
    record_data = {
        "schema_version": "0.8.0",
        "name": f"mcp-complete-test-{int(time.time())}",
        "version": "v1.0.0",
        "description": "MCP complete test",
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
    
    # 3. Wait for propagation
    print("\n3️⃣  Wait 70s for publication")
    await asyncio.sleep(70)
    
    # 4. Search from Node 2
    print("\n4️⃣  SEARCH from Node 2")
    peer_addr = None
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
                    break
    
    if not peer_addr:
        print("   ❌ Record not found in search results")
        return False
    
    print(f"   ✅ Found CID: {cid}")
    print(f"   📍 Peer Address: {peer_addr}")
    
    # 5. Sync from Node 1 to Node 2
    print("\n5️⃣  SYNC from Node 1 to Node 2")
    async with stdio_client(server_params_2) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            sync_result = await session.call_tool("sync_create", {
                "remote_url": "sn-dir1.labs.outshift.com:8888",
                "cids": [cid]
            })
            sync_data = json.loads(sync_result.content[0].text)
            sync_id = sync_data["sync_id"]
            print(f"   ✅ Sync ID: {sync_id}")
    
    # Wait for sync to complete
    print("   ⏳ Waiting for sync...")
    for i in range(6):
        await asyncio.sleep(10)
        async with stdio_client(server_params_2) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                status_result = await session.call_tool("sync_status", {"sync_id": sync_id})
                status_data = json.loads(status_result.content[0].text)
                
                if status_data.get("status") not in ["SYNC_STATUS_PENDING", "SYNC_STATUS_IN_PROGRESS"]:
                    print(f"   ✅ Sync completed")
                    break
    
    # Extra wait
    await asyncio.sleep(5)
    
    # 6. Pull from Node 2
    print("\n6️⃣  PULL from Node 2 (after sync)")
    async with stdio_client(server_params_2) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            pull_result = await session.call_tool("pull", {"cid": cid})
            pull_data = json.loads(pull_result.content[0].text)
            print(f"   ✅ Pulled: {pull_data.get('name', 'Unknown')}")
    
    print("\n" + "=" * 50)
    print("✅ MCP SERVER TEST PASSED!")
    print("=" * 50)
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(test_complete_federation())
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
