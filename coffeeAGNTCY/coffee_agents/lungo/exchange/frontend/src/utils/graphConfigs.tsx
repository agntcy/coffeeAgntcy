/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { TiWeatherCloudy } from "react-icons/ti"
import supervisorIcon from "@/assets/supervisor.png"
import farmAgentIcon from "@/assets/Grader-Agent.png"
import { FarmName } from "./const"
import { logger } from "./logger"

export interface GraphConfig {
  title: string
  nodes: any[]
  edges: any[]
  animationSequence: { ids: string[] }[]
}

const DEFAULT_EXCHANGE_APP_API_URL = "http://127.0.0.1:8000"
const EXCHANGE_APP_API_URL =
  (import.meta.env as any).VITE_EXCHANGE_APP_API_URL ||
  DEFAULT_EXCHANGE_APP_API_URL

const CoffeeBeanIcon = (
  <img
    src={farmAgentIcon}
    alt="Coffee Farm Agent Icon"
    className="h-4 w-4 object-contain opacity-100 brightness-0 invert"
  />
)

const GraderAgentIcon = (
  <img
    src={farmAgentIcon}
    alt="Grader Agent Icon"
    className="h-4 w-4 object-contain opacity-100 brightness-0 invert"
  />
)

const commonNodeData = {
  backgroundColor: "#F5F5F5",
}

const SLIM_A2A_CONFIG: GraphConfig = {
  title: "SLIM A2A Coffee Agent Communication",
  nodes: [
    {
      id: "1",
      type: "customNode",
      data: {
        ...commonNodeData,
        icon: (
          <img
            src={supervisorIcon}
            alt="Supervisor Icon"
            className="h-4 w-4 object-contain brightness-0 invert"
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
        ...commonNodeData,
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

const SLIM_MULTI_A2A_CONFIG: GraphConfig = {
  title: "SLIM Multi A2A Coffee Farm Network",
  nodes: [
    {
      id: "1",
      type: "customNode",
      data: {
        ...commonNodeData,
        icon: (
          <img
            src={supervisorIcon}
            alt="Supervisor Icon"
            className="h-4 w-4 object-contain brightness-0 invert"
          />
        ),
        label1: "Supervisor Agent",
        label2: "Buyer",
        handles: "source",
        githubLink:
          "https://github.com/agntcy/coffeeAgntcy/blob/main/coffeeAGNTCY/coffee_agents/lungo/exchange/graph/graph.py#L50",
        agentDirectoryLink: "https://agent-directory.outshift.com/explore",
      },
      position: { x: 527.1332569384248, y: 76.4805787605829 },
    },
    {
      id: "2",
      type: "transportNode",
      data: {
        ...commonNodeData,
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
        ...commonNodeData,
        icon: CoffeeBeanIcon,
        label1: "Brazil",
        label2: "Coffee Farm Agent",
        handles: "target",
        farmName: FarmName?.BrazilCoffeeFarm || "Brazil Coffee Farm",
        verificationStatus: "failed",
        githubLink:
          "https://github.com/agntcy/coffeeAgntcy/blob/main/coffeeAGNTCY/coffee_agents/lungo/farms/brazil/agent.py#L30",
        agentDirectoryLink: "https://agent-directory.outshift.com/explore",
      },

      position: { x: 232.0903941835277, y: 503.93174725714437 },
    },
    {
      id: "4",
      type: "customNode",
      data: {
        ...commonNodeData,
        icon: CoffeeBeanIcon,
        label1: "Colombia",
        label2: "Coffee Farm Agent",
        handles: "all",
        farmName: FarmName?.ColombiaCoffeeFarm || "Colombia Coffee Farm",
        verificationStatus: "verified",
        githubLink:
          "https://github.com/agntcy/coffeeAgntcy/blob/main/coffeeAGNTCY/coffee_agents/lungo/farms/colombia/agent.py#L54",
        agentDirectoryLink: "https://agent-directory.outshift.com/explore",
      },
      position: { x: 521.266082170288, y: 505.38817113883306 },
    },
    {
      id: "5",
      type: "customNode",
      data: {
        ...commonNodeData,
        icon: CoffeeBeanIcon,
        label1: "Vietnam",
        label2: "Coffee Farm Agent",
        handles: "target",
        farmName: FarmName?.VietnamCoffeeFarm || "Vietnam Coffee Farm",
        verificationStatus: "verified",
        githubLink:
          "https://github.com/agntcy/coffeeAgntcy/blob/main/coffeeAGNTCY/coffee_agents/lungo/farms/vietnam/agent.py#L30",
        agentDirectoryLink: "https://agent-directory.outshift.com/explore",
      },
      position: { x: 832.9824511707582, y: 505.08339631990395 },
    },
    {
      id: "6",
      type: "customNode",
      data: {
        ...commonNodeData,
        icon: <TiWeatherCloudy className="h-4 w-4 text-white" />,
        label1: "MCP Server",
        label2: "Weather",
        handles: "target",
        githubLink:
          "https://github.com/agntcy/coffeeAgntcy/blob/main/coffeeAGNTCY/coffee_agents/lungo/mcp_servers/weather_service.py#L25",
        agentDirectoryLink: "https://agent-directory.outshift.com/explore",
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

export const getGraphConfig = (pattern: string): GraphConfig => {
  switch (pattern) {
    case "slim_a2a":
      return SLIM_A2A_CONFIG
    case "slim_multi_a2a":
      return SLIM_MULTI_A2A_CONFIG
    default:
      return SLIM_MULTI_A2A_CONFIG
  }
}

export const updateTransportLabels = async (
  setNodes: (updater: (nodes: any[]) => any[]) => void,
  setEdges: (updater: (edges: any[]) => any[]) => void,
): Promise<void> => {
  try {
    const response = await fetch(`${EXCHANGE_APP_API_URL}/transport/config`)
    const data = await response.json()
    const transport = data.transport

    setNodes((nodes: any[]) =>
      nodes.map((node: any) =>
        node.id === "2"
          ? {
              ...node,
              data: { ...node.data, label: `Transport: ${transport}` },
            }
          : node,
      ),
    )

    setEdges((edges: any[]) =>
      edges.map((edge: any) =>
        edge.id === "4-6"
          ? { ...edge, data: { ...edge.data, label: `MCP: ${transport}` } }
          : edge,
      ),
    )
  } catch (error) {
    logger.apiError("/transport/config", error)
  }
}
