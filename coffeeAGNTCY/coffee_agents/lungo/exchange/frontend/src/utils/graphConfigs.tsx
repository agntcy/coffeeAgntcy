/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { TiWeatherCloudy } from "react-icons/ti"
import supervisorIcon from "@/assets/supervisor.png"
import farmAgentIcon from "@/assets/Grader-Agent.png"
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

const POSITION_MAP: Record<string, { x: number; y: number }> = {
  "1": { x: 527.1332569384248, y: 76.4805787605829 },
  "2": { x: 229.02370449534635, y: 284.688426426175 },
  "3": { x: 232.0903941835277, y: 503.93174725714437 },
  "4": { x: 521.266082170288, y: 505.38817113883306 },
  "5": { x: 832.9824511707582, y: 505.08339631990395 },
  "6": { x: 569.3959708104304, y: 731.9104402412228 },
}

const getNodeIcon = (serverNode: any) => {
  if (serverNode.type === "transportNode") {
    return null
  }

  if (serverNode.name?.includes("Supervisor")) {
    return (
      <img
        src={supervisorIcon}
        alt="Supervisor Icon"
        className="h-4 w-4 object-contain brightness-0 invert"
      />
    )
  }

  if (
    serverNode.name?.includes("MCP Server") ||
    serverNode.data?.label2 === "Weather"
  ) {
    return <TiWeatherCloudy className="h-4 w-4 text-white" />
  }

  return CoffeeBeanIcon
}

const generateNodesFromServer = (serverNodes: any[]) => {
  return serverNodes.map((serverNode: any) => ({
    id: serverNode.id,
    type: serverNode.type,
    data: {
      icon: getNodeIcon(serverNode),

      ...serverNode.data,

      githubLink: serverNode.github_url || "",
    },
    position: POSITION_MAP[serverNode.id] || { x: 0, y: 0 },
  }))
}

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
  nodes: [],
  edges: [],
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
    case "publish_subscribe":
      return PUBLISH_SUBSCRIBE_CONFIG
    default:
      return PUBLISH_SUBSCRIBE_CONFIG
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
              data: {
                ...node.data,
                label: `Transport: ${transport}`,
              },
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

export const updateTopologyFromServer = async (
  pattern: string,
  setNodes: (updater: (nodes: any[]) => any[]) => void,
  setEdges: (updater: (edges: any[]) => any[]) => void,
  setLoading?: (loading: boolean) => void,
  onComplete?: () => void,
): Promise<void> => {
  try {
    if (setLoading) setLoading(true)

    const response = await fetch(
      `${EXCHANGE_APP_API_URL}/topology?pattern=${pattern}`,
    )
    const data = await response.json()

    const dynamicNodes = generateNodesFromServer(data.nodes)
    setNodes(() => dynamicNodes)

    if (data.edges && data.edges.length > 0) {
      setEdges(() => data.edges)
    }

    if (setLoading) setLoading(false)

    if (onComplete) {
      setTimeout(() => {
        onComplete()
      }, 100)
    }
  } catch (error) {
    logger.apiError("/topology", error)
    if (setLoading) setLoading(false)
  }
}
