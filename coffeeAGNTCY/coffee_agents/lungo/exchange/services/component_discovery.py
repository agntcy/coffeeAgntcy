# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import List
from pydantic import BaseModel, Field

from farms.brazil.card import AGENT_CARD as brazil_agent_card
from farms.colombia.card import AGENT_CARD as colombia_agent_card  
from farms.vietnam.card import AGENT_CARD as vietnam_agent_card
from config.config import (
    DEFAULT_MESSAGE_TRANSPORT,
    IDENTITY_API_KEY,
    IDENTITY_API_SERVER_URL,
)
from services.identity_service_impl import IdentityServiceImpl

logger = logging.getLogger(__name__)


class TopologyNode(BaseModel):
    id: str  # Semantic ID (e.g., "1", "2", "3")
    type: str  # UI component type (e.g., "customNode", "transportNode")
    name: str
    verification: str = None  
    github_url: str = None
    data: dict = {}  # All UI-specific data properties 

class TopologyEdge(BaseModel):
    id: str  # Edge ID in format "source-target"
    source: str  # Source node ID
    target: str  # Target node ID
    source_handle: str = None  # Source handle for positioning
    target_handle: str = None  # Target handle for positioning
    data: dict = {}  # Edge data including label
    type: str = "custom"  # UI edge type 
    
class TopologyComponents(BaseModel):
    nodes: List[TopologyNode]
    edges: List[TopologyEdge]
    transport: str


class ComponentDiscoveryService:
    """
    Simple service to return topology structure using existing farm cards and configuration.
    Uses the same farm list as the existing tools: brazil, colombia, vietnam.
    """
    
    def __init__(self):
        self.identity_service = IdentityServiceImpl(
            api_key=IDENTITY_API_KEY,
            base_url=IDENTITY_API_SERVER_URL
        )
    
    async def discover_components(self, pattern: str) -> TopologyComponents:
        """
        Discover topology components for the given pattern.
        This is the method called by the API endpoint.
        
        Args:
            pattern: The topology pattern name (e.g., "publish_subscribe")
            
        Returns:
            TopologyComponents: Nodes, edges, labels and transport info
        """
        return await self.get_components_by_pattern(pattern)
    
    async def get_components_by_pattern(self, pattern: str) -> TopologyComponents:
        """
        Return topology structure for the given pattern using existing configuration.
        
        Args:
            pattern: The topology pattern name (e.g., "publish_subscribe")
            
        Returns:
            TopologyComponents: Nodes, edges, and transport info
        """
        logger.info(f"Getting topology components for pattern: {pattern}")
        
        if pattern == "publish_subscribe":
            return await self._get_publish_subscribe_topology()
        else:
            raise ValueError(f"Unsupported pattern: {pattern}. Only publish_subscribe is supported.")
    
    async def _get_publish_subscribe_topology(self) -> TopologyComponents:
        """Build topology for publish-subscribe pattern."""
        logger.info("Building publish-subscribe topology")
        
        nodes = []
        edges = []
        
        nodes.append(TopologyNode(
            id="1",
            type="customNode", 
            name="Supervisor Agent",
            github_url="https://github.com/agntcy/coffeeAgntcy/blob/main/coffeeAGNTCY/coffee_agents/lungo/exchange/graph/graph.py#L50",
            data={
                "label1": "Supervisor Agent",
                "label2": "Buyer", 
                "agentDirectoryLink": "https://agent-directory.outshift.com/explore"
            }
        ))
        
        transport_github_urls = {
            "NATS": "https://github.com/agntcy/app-sdk/blob/main/src/agntcy_app_sdk/transports/nats/transport.py#L21",
            "SLIM": "https://github.com/agntcy/app-sdk/blob/main/src/agntcy_app_sdk/transports/slim/transport.py#L23"
        }
        
        nodes.append(TopologyNode(
            id="2",
            type="transportNode",
            name=f"Transport: {DEFAULT_MESSAGE_TRANSPORT.upper()}",
            github_url=transport_github_urls[DEFAULT_MESSAGE_TRANSPORT.upper()],
            data={
                "label": f"Transport: {DEFAULT_MESSAGE_TRANSPORT.upper()}"
            }
        ))
        
        edges.append(TopologyEdge(
            id="1-2",
            source="1",
            target="2",
            target_handle="top",
            data={"label": "A2A"},
            type="custom"
        ))
        
        farm_data = [
            (brazil_agent_card, "https://github.com/agntcy/coffeeAgntcy/blob/main/coffeeAGNTCY/coffee_agents/lungo/farms/brazil/agent.py#L30"),
            (colombia_agent_card, "https://github.com/agntcy/coffeeAgntcy/blob/main/coffeeAGNTCY/coffee_agents/lungo/farms/colombia/agent.py#L54"),
            (vietnam_agent_card, "https://github.com/agntcy/coffeeAgntcy/blob/main/coffeeAGNTCY/coffee_agents/lungo/farms/vietnam/agent.py#L30")
        ]
        
        for i, (farm_card, github_url) in enumerate(farm_data):
            farm_id = str(i + 3)  # Start from 3 to match graphConfig IDs (3=Brazil, 4=Colombia, 5=Vietnam)
            
            farm_name = farm_card.name.replace(" Coffee Farm", "").strip()
            
            verification_status = await self._get_farm_verification_status(farm_card.name)
            
            nodes.append(TopologyNode(
                id=farm_id,
                type="customNode",
                name=farm_name, 
                verification=verification_status,
                github_url=github_url,
                data={
                    "label1": farm_name,
                    "label2": "Coffee Farm Agent",
                    "farmName": farm_name,
                    "verificationStatus": verification_status,
                    "agentDirectoryLink": "https://agent-directory.outshift.com/explore"
                }
            ))
            
            # Transport connects to farm with appropriate source handle
            source_handle = None
            if farm_id == "3":  # Brazil
                source_handle = "bottom_left"
            elif farm_id == "4":  # Colombia  
                source_handle = "bottom_center"
            elif farm_id == "5":  # Vietnam
                source_handle = "bottom_right"
                
            edges.append(TopologyEdge(
                id=f"2-{farm_id}",
                source="2",
                target=farm_id,
                source_handle=source_handle,
                data={"label": "A2A"},
                type="custom"
            ))
        
        nodes.append(TopologyNode(
            id="6",
            type="customNode",
            name="MCP Server",  
            github_url="https://github.com/agntcy/coffeeAgntcy/blob/main/coffeeAGNTCY/coffee_agents/lungo/mcp_servers/weather_service.py#L25",
            data={
                "label1": "MCP Server",
                "label2": "Weather",
                "agentDirectoryLink": "https://agent-directory.outshift.com/explore"
            }
        ))
        
        # Colombia farm (ID: 4) connects to weather MCP
        edges.append(TopologyEdge(
            id="4-6",
            source="4",
            target="6",
            data={"label": f"MCP: {DEFAULT_MESSAGE_TRANSPORT.upper()}"},
            type="custom"
        ))
        
        logger.info(f"Built topology with {len(nodes)} nodes and {len(edges)} edges")
        return TopologyComponents(
            nodes=nodes,
            edges=edges,
            transport=DEFAULT_MESSAGE_TRANSPORT.upper()
        )
    
    async def _get_farm_verification_status(self, farm_name: str) -> str:
        """Get verification status for a farm using existing identity service patterns."""
        try:
            logger.debug(f"Checking verification status for farm: {farm_name}")
            
            apps_response = self.identity_service.get_all_apps()
            
            farm_app = None
            for app in apps_response.apps:
                if app.name.lower() == farm_name.lower():
                    farm_app = app
                    break
            
            if farm_app:
                logger.debug(f"Found farm app: {farm_app.name} with status: {farm_app.status}")
                
                try:
                    badge = self.identity_service.get_badge_for_app(farm_app.id)
                    
                    verification_result = self.identity_service.verify_badges(badge)
                    
                    if verification_result and verification_result.get("status") is True:
                        return "verified"
                    else:
                        return "unverified"
                        
                except Exception as badge_error:
                    logger.warning(f"Could not get/verify badge for farm {farm_name}: {badge_error}")
                    return "unverified"
            else:
                logger.warning(f"Farm app not found for {farm_name}")
                return "unverified"
                
        except Exception as e:
            logger.warning(f"Could not verify farm {farm_name} via identity service: {e}")
            return "failed"
