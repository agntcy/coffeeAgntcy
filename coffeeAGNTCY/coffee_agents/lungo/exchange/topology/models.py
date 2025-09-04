# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import List
from pydantic import BaseModel


class TopologyNode(BaseModel):
    id: str  
    type: str  
    name: str
    verification: str = None  
    github_url: str = None
    data: dict = {} 


class TopologyEdge(BaseModel):
    id: str  
    source: str  
    target: str 
    source_handle: str = None  
    target_handle: str = None  
    data: dict = {}  
    type: str = "custom"  
    

class TopologyComponents(BaseModel):
    nodes: List[TopologyNode]
    edges: List[TopologyEdge]
    transport: str
