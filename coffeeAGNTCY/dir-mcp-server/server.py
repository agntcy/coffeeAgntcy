#!/usr/bin/env python3
"""
Directory MCP Server

An MCP server that provides directory operations using the AGNTCY Directory Python SDK.
Supports multi-node connections and federated search.
"""

import asyncio
import json
import logging
import os
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dir-mcp-server")

# Lazy import to handle SDK availability
try:
    from agntcy.dir_sdk.client import Client, Config
    SDK_AVAILABLE = True
except ImportError:
    logger.warning("agntcy-dir not available, using mock mode")
    SDK_AVAILABLE = False


class DirectoryMCPServer:
    """MCP server for directory operations with multi-node support"""
    
    def __init__(self):
        self.default_node = os.getenv("DIRECTORY_SERVER_ADDRESS", "localhost:8888")
        spiffe_socket_raw = os.getenv("SPIFFE_SOCKET_PATH", "/run/spire/sockets/agent.sock")
        # Add unix:// scheme if not present
        if spiffe_socket_raw and not spiffe_socket_raw.startswith("unix://"):
            self.spiffe_socket = f"unix://{spiffe_socket_raw}"
        else:
            self.spiffe_socket = spiffe_socket_raw
        self.auth_mode = os.getenv("AUTH_MODE", "x509")  # x509 or jwt
        self.jwt_audience = os.getenv("JWT_AUDIENCE", "")
        self.nodes = {}  # Cache of clients by node address
        logger.info(f"Initialized with default node: {self.default_node}")
        logger.info(f"Auth mode: {self.auth_mode}, SPIFFE socket: {self.spiffe_socket}")
    
    def get_client(self, node_address: str = None):
        """Get or create client for specific node"""
        if not SDK_AVAILABLE:
            raise RuntimeError("Directory SDK not available")
        
        addr = node_address or self.default_node
        if addr not in self.nodes:
            # Check if SPIFFE socket exists (strip unix:// prefix for check)
            socket_path = self.spiffe_socket.replace("unix://", "") if self.spiffe_socket else ""
            if socket_path and os.path.exists(socket_path):
                logger.info(f"Using SPIFFE authentication for {addr}")
                config = Config(
                    server_address=addr,
                    spiffe_socket_path=self.spiffe_socket,
                    auth_mode=self.auth_mode,
                    jwt_audience=self.jwt_audience if self.auth_mode == "jwt" else ""
                )
            else:
                logger.info(f"Using insecure mode for {addr} (SPIFFE socket not found)")
                config = Config(server_address=addr)
            
            self.nodes[addr] = Client(config)
            logger.info(f"Created client for node: {addr}")
        return self.nodes[addr]
    
    async def search(self, name: str = None, skill: str = None, node: str = None) -> dict[str, Any]:
        """Search for agents in the directory"""
        client = self.get_client(node)
        
        logger.info(f"Searching - name: {name}, skill: {skill}")
        
        from agntcy.dir_sdk.models import search_v1
        
        # Build search queries
        queries = []
        if name:
            queries.append(search_v1.RecordQuery(
                type=search_v1.RECORD_QUERY_TYPE_NAME,
                value=name
            ))
        if skill:
            queries.append(search_v1.RecordQuery(
                type=search_v1.RECORD_QUERY_TYPE_SKILL_NAME,
                value=skill
            ))
        
        # Use SearchCIDs to get CIDs, then SearchRecords to get data
        cid_req = search_v1.SearchCIDsRequest(queries=queries, limit=100)
        
        # SDK methods are synchronous, run in executor
        loop = asyncio.get_event_loop()
        cid_responses = await loop.run_in_executor(
            None, 
            lambda: list(client.search_cids(cid_req))
        )
        
        # Get CIDs
        cids = [r.record_cid for r in cid_responses]
        
        # Now get full records
        record_req = search_v1.SearchRecordsRequest(queries=queries, limit=100)
        record_responses = await loop.run_in_executor(
            None, 
            lambda: list(client.search_records(record_req))
        )
        
        # Convert protobuf Struct to dict and add CID
        from google.protobuf.json_format import MessageToDict
        results = []
        for i, r in enumerate(record_responses):
            if hasattr(r, 'record') and i < len(cids):
                data = MessageToDict(r.record.data)
                data['cid'] = cids[i]  # Add CID from SearchCIDs response
                results.append(data)
        
        return {
            "results": results,
            "count": len(results)
        }
    
    async def pull(self, cid: str, node: str = None) -> dict[str, Any]:
        """Pull a record by CID"""
        client = self.get_client(node)
        logger.info(f"Pulling CID: {cid}")
        
        from agntcy.dir_sdk.models import core_v1
        from google.protobuf.json_format import MessageToDict
        
        ref = core_v1.RecordRef(cid=cid)
        loop = asyncio.get_event_loop()
        records = await loop.run_in_executor(None, lambda: client.pull([ref]))
        
        if records:
            return MessageToDict(records[0].data)
        return {}
    
    async def export(self, cid: str, target_format: str = "a2a", node: str = None) -> dict[str, Any]:
        """Export a record to a different format"""
        client = self.get_client(node)
        logger.info(f"Exporting CID {cid} to format: {target_format}")
        
        from agntcy.dir_sdk.models import core_v1
        
        ref = core_v1.RecordRef(cid=cid)
        loop = asyncio.get_event_loop()
        records = await loop.run_in_executor(None, lambda: client.pull([ref]))
        
        if not records:
            return {}
        
        record_data = records[0].data
        
        # Extract the target module if it exists
        if "modules" in record_data:
            for module in record_data.get("modules", []):
                if module.get("type") == target_format:
                    return module.get("data", {})
        
        return record_data
    
    async def push(self, record: dict[str, Any], node: str = None) -> dict[str, Any]:
        """Push a record to the directory"""
        client = self.get_client(node)
        logger.info(f"Pushing record: {record.get('name', 'Unknown')}")
        
        from agntcy.dir_sdk.models import core_v1
        
        record_obj = core_v1.Record(data=record)
        loop = asyncio.get_event_loop()
        refs = await loop.run_in_executor(None, lambda: client.push([record_obj]))
        return {"cid": refs[0].cid, "success": True}
    
    async def delete(self, cid: str, node: str = None) -> dict[str, Any]:
        """Delete a record from the directory"""
        client = self.get_client(node)
        logger.info(f"Deleting CID: {cid}")
        
        from agntcy.dir_sdk.models import core_v1
        
        ref = core_v1.RecordRef(cid=cid)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: client.delete([ref]))
        return {"cid": cid, "success": True, "deleted": True}
    
    async def routing_publish(self, cid: str, node: str = None) -> dict[str, Any]:
        """Publish a record to the routing network"""
        client = self.get_client(node)
        logger.info(f"Publishing CID to routing network: {cid}")
        
        from agntcy.dir_sdk.models import routing_v1, core_v1
        
        ref = core_v1.RecordRef(cid=cid)
        publish_req = routing_v1.PublishRequest(
            record_refs=routing_v1.RecordRefs(refs=[ref])
        )
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: client.publish(publish_req))
        return {"success": True, "published": cid}
    
    async def routing_unpublish(self, cid: str, node: str = None) -> dict[str, Any]:
        """Unpublish a record from the routing network"""
        client = self.get_client(node)
        logger.info(f"Unpublishing CID from routing network: {cid}")
        
        from agntcy.dir_sdk.models import routing_v1, core_v1
        
        ref = core_v1.RecordRef(cid=cid)
        unpublish_req = routing_v1.UnpublishRequest(
            record_refs=routing_v1.RecordRefs(refs=[ref])
        )
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: client.unpublish(unpublish_req))
        return {"success": True, "unpublished": cid}
    
    async def routing_search(self, skill: str = None, domain: str = None, limit: int = 10, node: str = None) -> dict[str, Any]:
        """Search for records across the federated network"""
        client = self.get_client(node)
        logger.info(f"Routing search - skill: {skill}, domain: {domain}, limit: {limit}")
        
        from agntcy.dir_sdk.models import routing_v1
        
        queries = []
        if skill:
            queries.append(routing_v1.RecordQuery(
                type=routing_v1.RECORD_QUERY_TYPE_SKILL,
                value=skill
            ))
        if domain:
            queries.append(routing_v1.RecordQuery(
                type=routing_v1.RECORD_QUERY_TYPE_DOMAIN,
                value=domain
            ))
        
        search_req = routing_v1.SearchRequest(queries=queries)
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: list(client.routing_client.Search(search_req))
        )
        
        return {
            "results": [
                {
                    "record_ref": {"cid": r.record_ref.cid},
                    "peer": {"addrs": list(r.peer.addrs)}
                }
                for r in results
            ],
            "count": len(results)
        }
    
    async def sync_create(self, remote_url: str, cids: list[str] = None, node: str = None) -> dict[str, Any]:
        """Create a sync operation to pull records from a remote directory"""
        client = self.get_client(node)
        logger.info(f"Creating sync from {remote_url} with {len(cids) if cids else 'all'} CIDs")
        
        from agntcy.dir.store.v1 import sync_service_pb2
        
        sync_req = sync_service_pb2.CreateSyncRequest(
            remote_directory_url=remote_url,
            cids=cids if cids else []
        )
        loop = asyncio.get_event_loop()
        sync_resp = await loop.run_in_executor(None, lambda: client.create_sync(sync_req))
        return {"sync_id": sync_resp.sync_id, "remote_url": remote_url, "success": True}
    
    async def sync_status(self, sync_id: str, node: str = None) -> dict[str, Any]:
        """Get the status of a sync operation"""
        client = self.get_client(node)
        logger.info(f"Getting sync status for: {sync_id}")
        
        from agntcy.dir.store.v1 import sync_service_pb2
        
        status_req = sync_service_pb2.GetSyncRequest(sync_id=sync_id)
        loop = asyncio.get_event_loop()
        status = await loop.run_in_executor(None, lambda: client.get_sync(status_req))
        
        return {
            "sync_id": status.sync_id,
            "status": sync_service_pb2.SyncStatus.Name(status.status),
            "remote_url": status.remote_directory_url,
            "cids": list(status.cids)
        }


# Create MCP server
server = Server("directory-mcp-server")
dir_server = DirectoryMCPServer()


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available directory tools"""
    return [
        Tool(
            name="search",
            description="Search for agents in the directory by name or skill",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Agent name to search for (supports wildcards: *, ?)"
                    },
                    "skill": {
                        "type": "string",
                        "description": "Skill to search for"
                    },
                    "node": {
                        "type": "string",
                        "description": "Directory node address (optional, defaults to configured node)"
                    }
                }
            }
        ),
        Tool(
            name="pull",
            description="Pull a record by its Content ID (CID)",
            inputSchema={
                "type": "object",
                "properties": {
                    "cid": {
                        "type": "string",
                        "description": "Content ID of the record to pull"
                    },
                    "node": {
                        "type": "string",
                        "description": "Directory node address (optional)"
                    }
                },
                "required": ["cid"]
            }
        ),
        Tool(
            name="export",
            description="Export a record to a specific format (e.g., a2a)",
            inputSchema={
                "type": "object",
                "properties": {
                    "cid": {
                        "type": "string",
                        "description": "Content ID of the record to export"
                    },
                    "target_format": {
                        "type": "string",
                        "description": "Target format (default: a2a)",
                        "default": "a2a"
                    },
                    "node": {
                        "type": "string",
                        "description": "Directory node address (optional)"
                    }
                },
                "required": ["cid"]
            }
        ),
        Tool(
            name="push",
            description="Push a record to the directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "record": {
                        "type": "object",
                        "description": "OASF record to push"
                    },
                    "node": {
                        "type": "string",
                        "description": "Directory node address (optional)"
                    }
                },
                "required": ["record"]
            }
        ),
        Tool(
            name="delete",
            description="Delete a record from the directory by CID",
            inputSchema={
                "type": "object",
                "properties": {
                    "cid": {
                        "type": "string",
                        "description": "Content ID of the record to delete"
                    },
                    "node": {
                        "type": "string",
                        "description": "Directory node address (optional)"
                    }
                },
                "required": ["cid"]
            }
        ),
        Tool(
            name="routing_publish",
            description="Publish a record to the routing network for discovery",
            inputSchema={
                "type": "object",
                "properties": {
                    "cid": {
                        "type": "string",
                        "description": "Content ID of the record to publish"
                    },
                    "node": {
                        "type": "string",
                        "description": "Directory node address (optional)"
                    }
                },
                "required": ["cid"]
            }
        ),
        Tool(
            name="routing_unpublish",
            description="Unpublish a record from the routing network",
            inputSchema={
                "type": "object",
                "properties": {
                    "cid": {
                        "type": "string",
                        "description": "Content ID of the record to unpublish"
                    },
                    "node": {
                        "type": "string",
                        "description": "Directory node address (optional)"
                    }
                },
                "required": ["cid"]
            }
        ),
        Tool(
            name="routing_search",
            description="Search for records across the federated network (peer-to-peer discovery)",
            inputSchema={
                "type": "object",
                "properties": {
                    "skill": {
                        "type": "string",
                        "description": "Skill to search for"
                    },
                    "domain": {
                        "type": "string",
                        "description": "Domain to search for"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10)",
                        "default": 10
                    },
                    "node": {
                        "type": "string",
                        "description": "Directory node address (optional)"
                    }
                }
            }
        ),
        Tool(
            name="sync_create",
            description="Create a sync operation to pull records from a remote directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "remote_url": {
                        "type": "string",
                        "description": "URL of the remote directory (e.g., https://remote-dir.example.com)"
                    },
                    "cids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of CIDs to sync (optional, syncs all if not provided)"
                    },
                    "node": {
                        "type": "string",
                        "description": "Directory node address (optional)"
                    }
                },
                "required": ["remote_url"]
            }
        ),
        Tool(
            name="sync_status",
            description="Get the status of a sync operation",
            inputSchema={
                "type": "object",
                "properties": {
                    "sync_id": {
                        "type": "string",
                        "description": "Sync operation ID"
                    },
                    "node": {
                        "type": "string",
                        "description": "Directory node address (optional)"
                    }
                },
                "required": ["sync_id"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    try:
        if name == "search":
            result = await dir_server.search(
                name=arguments.get("name"),
                skill=arguments.get("skill"),
                node=arguments.get("node")
            )
        elif name == "pull":
            result = await dir_server.pull(
                cid=arguments["cid"],
                node=arguments.get("node")
            )
        elif name == "export":
            result = await dir_server.export(
                cid=arguments["cid"],
                target_format=arguments.get("target_format", "a2a"),
                node=arguments.get("node")
            )
        elif name == "push":
            result = await dir_server.push(
                record=arguments["record"],
                node=arguments.get("node")
            )
        elif name == "delete":
            result = await dir_server.delete(
                cid=arguments["cid"],
                node=arguments.get("node")
            )
        elif name == "routing_publish":
            result = await dir_server.routing_publish(
                cid=arguments["cid"],
                node=arguments.get("node")
            )
        elif name == "routing_unpublish":
            result = await dir_server.routing_unpublish(
                cid=arguments["cid"],
                node=arguments.get("node")
            )
        elif name == "routing_search":
            result = await dir_server.routing_search(
                skill=arguments.get("skill"),
                domain=arguments.get("domain"),
                limit=arguments.get("limit", 10),
                node=arguments.get("node")
            )
        elif name == "sync_create":
            result = await dir_server.sync_create(
                remote_url=arguments["remote_url"],
                cids=arguments.get("cids"),
                node=arguments.get("node")
            )
        elif name == "sync_status":
            result = await dir_server.sync_status(
                sync_id=arguments["sync_id"],
                node=arguments.get("node")
            )
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e)})
        )]


async def main():
    """Run the MCP server"""
    logger.info("Starting Directory MCP Server")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
