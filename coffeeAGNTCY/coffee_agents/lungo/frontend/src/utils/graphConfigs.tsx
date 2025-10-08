/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { TiWeatherCloudy } from "react-icons/ti"
import { Truck, Calculator } from "lucide-react"
import { Node, Edge } from "@xyflow/react"
import supervisorIcon from "@/assets/supervisor.png"
import farmAgentIcon from "@/assets/Grader-Agent.png"
import { FarmName } from "./const"
import { logger } from "./logger"

export interface GraphConfig {
  title: string
  nodes: Node[]
  edges: Edge[]
  animationSequence: { ids: string[] }[]
}

const DEFAULT_EXCHANGE_APP_API_URL = "http://127.0.0.1:8000"
const EXCHANGE_APP_API_URL =
  import.meta.env.VITE_EXCHANGE_APP_API_URL || DEFAULT_EXCHANGE_APP_API_URL

const CoffeeBeanIcon = (
  <img
    src={farmAgentIcon}
    alt="Coffee Farm Agent Icon"
    className="dark-icon h-4 w-4 object-contain opacity-100"
  />
)

const GraderAgentIcon = (
  <img
    src={farmAgentIcon}
    alt="Grader Agent Icon"
    className="dark-icon h-4 w-4 object-contain opacity-100"
  />
)

const SLIM_A2A_CONFIG: GraphConfig = {
  title: "SLIM A2A Coffee Agent Communication",
  nodes: [
    {
      id: "1",
      type: "customNode",
      data: {
        icon: (
          <img
            src={supervisorIcon}
            alt="Supervisor Icon"
            className="dark-icon h-4 w-4 object-contain"
          />
        ),
        label1: "Supervisor Agent",
        label2: "Buyer",
        handles: "source",
        verificationStatus: "verified",
        githubLink:
          "https://github.com/agntcy/coffeeAgntcy/tree/main/coffeeAGNTCY/coffee_agents/corto/exchange",
        agentDirectoryLink: "https://agent-directory.outshift.com/explore",
      },
      position: { x: 529.1332569384248, y: 159.4805787605829 },
    },
    {
      id: "2",
      type: "customNode",
      data: {
        icon: GraderAgentIcon,
        label1: "Grader Agent",
        label2: "Sommelier",
        handles: "target",
        githubLink:
          "https://github.com/agntcy/coffeeAgntcy/tree/main/coffeeAGNTCY/coffee_agents/corto/farm",
        agentDirectoryLink: "https://agent-directory.outshift.com/explore",
      },
      position: { x: 534.0903941835277, y: 582.9317472571444 },
    },
  ],
  edges: [
    {
      id: "1-2",
      source: "1",
      target: "2",
      data: { label: "A2A" },
      type: "custom",
    },
  ],
  animationSequence: [{ ids: ["1"] }, { ids: ["1-2"] }, { ids: ["2"] }],
}

const PUBLISH_SUBSCRIBE_CONFIG: GraphConfig = {
  title: "Publish Subscribe Coffee Farm Network",
  nodes: [
    {
      id: "1",
      type: "customNode",
      data: {
        icon: (
          <img
            src={supervisorIcon}
            alt="Supervisor Icon"
            className="dark-icon h-4 w-4 object-contain"
          />
        ),
        label1: "Auction Agent",
        label2: "Buyer",
        handles: "source",
        githubLink:
          "https://github.com/agntcy/coffeeAgntcy/blob/main/coffeeAGNTCY/coffee_agents/lungo/agents/supervisors/auction/graph/graph.py#L116",
        agentDirectoryLink:
          "https://agent-directory.outshift.com/explore/34f05b1e-3bd3-4a21-b8c5-e9f191942ed0",
      },
      position: { x: 527.1332569384248, y: 76.4805787605829 },
    },
    {
      id: "2",
      type: "transportNode",
      data: {
        label: "Transport: ",
        githubLink:
          "https://github.com/agntcy/app-sdk/tree/main/src/agntcy_app_sdk/transports",
      },
      position: { x: 229.02370449534635, y: 284.688426426175 },
    },
    {
      id: "3",
      type: "customNode",
      data: {
        icon: CoffeeBeanIcon,
        label1: "Brazil",
        label2: "Coffee Farm Agent",
        handles: "target",
        farmName: FarmName?.BrazilCoffeeFarm || "Brazil Coffee Farm",
        verificationStatus: "failed",
        githubLink:
          "https://github.com/agntcy/coffeeAgntcy/blob/main/coffeeAGNTCY/coffee_agents/lungo/agents/farms/brazil/agent.py#L30",
        agentDirectoryLink:
          "https://agent-directory.outshift.com/explore/f52e742d-f9fc-41f5-a431-23ca69c4ef65",
      },

      position: { x: 232.0903941835277, y: 503.93174725714437 },
    },
    {
      id: "4",
      type: "customNode",
      data: {
        icon: CoffeeBeanIcon,
        label1: "Colombia",
        label2: "Coffee Farm Agent",
        handles: "all",
        farmName: FarmName?.ColombiaCoffeeFarm || "Colombia Coffee Farm",
        verificationStatus: "verified",
        githubLink:
          "https://github.com/agntcy/coffeeAgntcy/blob/main/coffeeAGNTCY/coffee_agents/lungo/agents/farms/colombia/agent.py#L53",
        agentDirectoryLink:
          "https://agent-directory.outshift.com/explore/1991a0f9-a24d-4197-902a-3de0a0c5920a",
      },
      position: { x: 521.266082170288, y: 505.38817113883306 },
    },
    {
      id: "5",
      type: "customNode",
      data: {
        icon: CoffeeBeanIcon,
        label1: "Vietnam",
        label2: "Coffee Farm Agent",
        handles: "target",
        farmName: FarmName?.VietnamCoffeeFarm || "Vietnam Coffee Farm",
        verificationStatus: "verified",
        githubLink:
          "https://github.com/agntcy/coffeeAgntcy/blob/main/coffeeAGNTCY/coffee_agents/lungo/agents/farms/vietnam/agent.py#L29",
        agentDirectoryLink:
          "https://agent-directory.outshift.com/explore/6907d9f6-6fea-4e2c-93d6-ab7914204a6f",
      },
      position: { x: 832.9824511707582, y: 505.08339631990395 },
    },
    {
      id: "6",
      type: "customNode",
      data: {
        icon: <TiWeatherCloudy className="dark-icon h-4 w-4" />,
        label1: "MCP Server",
        label2: "Weather",
        handles: "target",
        githubLink:
          "https://github.com/agntcy/coffeeAgntcy/blob/main/coffeeAGNTCY/coffee_agents/lungo/agents/mcp_servers/weather_service.py",
        agentDirectoryLink:
          "https://agent-directory.outshift.com/explore/8d720b8c-59a7-4ea4-9254-68c764e1f9b1",
      },
      position: { x: 569.3959708104304, y: 731.9104402412228 },
    },
  ],
  edges: [
    {
      id: "1-2",
      source: "1",
      target: "2",
      targetHandle: "top",
      data: { label: "A2A" },
      type: "custom",
    },
    {
      id: "2-3",
      source: "2",
      target: "3",
      sourceHandle: "bottom_left",
      data: { label: "A2A" },
      type: "custom",
    },
    {
      id: "2-4",
      source: "2",
      target: "4",
      sourceHandle: "bottom_center",
      data: { label: "A2A" },
      type: "custom",
    },
    {
      id: "2-5",
      source: "2",
      target: "5",
      sourceHandle: "bottom_right",
      data: { label: "A2A" },
      type: "custom",
    },
    {
      id: "4-6",
      source: "4",
      target: "6",
      data: { label: "MCP: " },
      type: "custom",
    },
  ],
  animationSequence: [
    { ids: ["1"] },
    { ids: ["1-2"] },
    { ids: ["2"] },
    { ids: ["2-3", "2-4", "2-5"] },
    { ids: ["3", "4", "5"] },
    { ids: ["4-6"] },
    { ids: ["6"] },
  ],
}

const GROUP_COMMUNICATION_CONFIG: GraphConfig = {
  title: "Secure Group Communication Logistics Network",
  nodes: [
    {
      id: "logistics-group",
      type: "group",
      data: {
        label: "Logistics Group",
      },
      position: { x: 50, y: 50 },
      style: {
        width: 900,
        height: 650,
        backgroundColor: "var(--group-background)",
        border: "none",
        borderRadius: "8px",
      },
    },
    {
      id: "1",
      type: "customNode",
      data: {
        icon: (
          <img
            src={supervisorIcon}
            alt="Supervisor Icon"
            className="dark-icon h-4 w-4 object-contain"
          />
        ),
        label1: "Logistics Agent",
        label2: "Buyer",
        handles: "source",
        githubLink:
          "https://github.com/agntcy/coffeeAgntcy/blob/main/coffeeAGNTCY/coffee_agents/lungo/agents/supervisors/auction/graph/graph.py#L116",
        agentDirectoryLink: "https://agent-directory.outshift.com/",
      },
      position: { x: 150, y: 100 },
      parentId: "logistics-group",
      extent: "parent",
    },
    {
      id: "2",
      type: "transportNode",
      data: {
        label: "Transport: SLIM",
        compact: true,
        githubLink:
          "https://github.com/agntcy/app-sdk/blob/main/src/agntcy_app_sdk/transports/slim/transport.py#L29",
      },
      position: { x: 380, y: 270 },
      parentId: "logistics-group",
      extent: "parent",
    },
    {
      id: "3",
      type: "customNode",
      data: {
        icon: (
          <img
            src={farmAgentIcon}
            alt="Farm Agent Icon"
            className="dark-icon h-4 w-4 object-contain opacity-100"
          />
        ),
        label1: "Tatooine",
        label2: "Coffee Farm Agent",
        handles: "source",
        farmName: "Tatooine Farm",
        githubLink:
          "https://github.com/agntcy/coffeeAgntcy/blob/main/coffeeAGNTCY/coffee_agents/lungo/agents/logistics/farm/agent.py#L30",
        agentDirectoryLink: "https://agent-directory.outshift.com/",
      },
      position: { x: 550, y: 100 },
      parentId: "logistics-group",
      extent: "parent",
    },
    {
      id: "4",
      type: "customNode",
      data: {
        icon: (
          <Truck className="dark-icon h-4 w-4 object-contain opacity-100" />
        ),
        label1: "Shipper",
        label2: "Shipper Agent",
        handles: "target",
        agentName: "Shipper Logistics",
        githubLink:
          "https://github.com/agntcy/coffeeAgntcy/blob/main/coffeeAGNTCY/coffee_agents/lungo/agents/logistics/shipper/agent.py#L30",
        agentDirectoryLink:
          "https://agent-directory.outshift.com/explore/shipper-logistics-agent",
      },
      position: { x: 150, y: 500 },
      parentId: "logistics-group",
      extent: "parent",
    },
    {
      id: "5",
      type: "customNode",
      data: {
        icon: (
          <Calculator className="dark-icon h-4 w-4 object-contain opacity-100" />
        ),
        label1: "Accountant",
        label2: "Accountant Agent",
        handles: "target",
        agentName: "Accountant Logistics",
        githubLink:
          "https://github.com/agntcy/coffeeAgntcy/blob/main/coffeeAGNTCY/coffee_agents/lungo/agents/logistics/accountant/agent.py#L30",
        agentDirectoryLink:
          "https://agent-directory.outshift.com/explore/accountant-logistics-agent",
      },
      position: { x: 500, y: 500 },
      parentId: "logistics-group",
      extent: "parent",
    },
  ],
  edges: [
    {
      id: "1-2",
      source: "1",
      target: "2",
      targetHandle: "top_left",
      data: { label: "A2A" },
      type: "custom",
    },
    {
      id: "3-2",
      source: "3",
      target: "2",
      targetHandle: "top_right",
      data: { label: "A2A" },
      type: "custom",
    },
    {
      id: "2-4",
      source: "2",
      target: "4",
      sourceHandle: "bottom_left",
      data: { label: "A2A" },
      type: "custom",
    },
    {
      id: "2-5",
      source: "2",
      target: "5",
      sourceHandle: "bottom_right",
      data: { label: "A2A" },
      type: "custom",
    },
  ],
  animationSequence: [
    { ids: ["1"] },
    { ids: ["1-2"] },
    { ids: ["2"] },
    { ids: ["3-2", "2-4", "2-5", "3", "4", "5"] },
    { ids: ["3"] },
    { ids: ["4"] },
    { ids: ["5"] },
    { ids: ["4"] },
  ],
}

export const getGraphConfig = (
  pattern: string,
  _isConnected?: boolean,
): GraphConfig => {
  switch (pattern) {
    case "slim_a2a":
      return SLIM_A2A_CONFIG
    case "publish_subscribe":
      return PUBLISH_SUBSCRIBE_CONFIG
    case "group_communication":
      return GROUP_COMMUNICATION_CONFIG
    default:
      return PUBLISH_SUBSCRIBE_CONFIG
  }
}

export const updateTransportLabels = async (
  setNodes: (updater: (nodes: any[]) => any[]) => void,
  setEdges: (updater: (edges: any[]) => any[]) => void,
  pattern?: string,
): Promise<void> => {
  if (pattern === "group_communication") {
    return
  }

  try {
    const response = await fetch(`${EXCHANGE_APP_API_URL}/transport/config`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    const data = await response.json()
    const transport = data.transport

    setNodes((nodes: any[]) =>
      nodes.map((node: any) =>
        node.id === "2"
          ? {
              ...node,
              data: {
                ...node.data,
                label: `Transport: ${transport}`,
                githubLink:
                  transport === "SLIM"
                    ? "https://github.com/agntcy/app-sdk/blob/main/src/agntcy_app_sdk/transports/slim/transport.py#L29"
                    : transport === "NATS"
                      ? "https://github.com/agntcy/app-sdk/blob/main/src/agntcy_app_sdk/transports/nats/transport.py#L27"
                      : "https://github.com/agntcy/app-sdk/tree/main/src/agntcy_app_sdk/transports",
              },
            }
          : node,
      ),
    )

    setEdges((edges: any[]) =>
      edges.map((edge: any) => {
        if (edge.id === "4-6") {
          return { ...edge, data: { ...edge.data, label: `MCP: ${transport}` } }
        }
        return edge
      }),
    )
  } catch (error) {
    logger.apiError("/transport/config", error)
  }
}
