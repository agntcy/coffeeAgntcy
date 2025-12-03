/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { TiWeatherCloudy } from "react-icons/ti"
import { Truck, Calculator } from "lucide-react"
import { Node, Edge } from "@xyflow/react"
import supervisorIcon from "@/assets/supervisor.png"
import farmAgentIcon from "@/assets/Grader-Agent.png"
import {
  FarmName,
  NODE_IDS,
  EDGE_IDS,
  NODE_TYPES,
  EDGE_TYPES,
  EDGE_LABELS,
  HANDLE_TYPES,
  VERIFICATION_STATUS,
} from "./const"
import { logger } from "./logger"
import urlsConfig from "./urls.json"
import { isGroupCommunication, getApiUrlForPattern } from "./patternUtils"

export interface GraphConfig {
  title: string
  nodes: Node[]
  edges: Edge[]
  animationSequence: { ids: string[] }[]
}

const CoffeeBeanIcon = (
  <img
    src={farmAgentIcon}
    alt="Coffee Farm Agent Icon"
    className="dark-icon h-4 w-4 object-contain opacity-100"
  />
)

const PUBLISH_SUBSCRIBE_CONFIG: GraphConfig = {
  title: "Publish Subscribe Coffee Farm Network",
  nodes: [
    {
      id: NODE_IDS.AUCTION_AGENT,
      type: NODE_TYPES.CUSTOM,
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
        handles: HANDLE_TYPES.SOURCE,
        verificationStatus: VERIFICATION_STATUS.VERIFIED,
        hasBadgeDetails: true,
        hasPolicyDetails: true,
        githubLink: `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.supervisorAuction}`,
        agentDirectoryLink: `${urlsConfig.agentDirectory.baseUrl}${urlsConfig.agentDirectory.agents.supervisorAuction}`,
      },
      position: { x: 527.1332569384248, y: 76.4805787605829 },
    },
    {
      id: NODE_IDS.TRANSPORT,
      type: NODE_TYPES.TRANSPORT,
      data: {
        label: "Transport: ",
        githubLink: `${urlsConfig.github.appSdkBaseUrl}${urlsConfig.github.transports.general}`,
      },
      position: { x: 229.02370449534635, y: 284.688426426175 },
    },
    {
      id: NODE_IDS.BRAZIL_FARM,
      type: NODE_TYPES.CUSTOM,
      data: {
        icon: CoffeeBeanIcon,
        label1: "Brazil",
        label2: "Coffee Farm Agent",
        handles: HANDLE_TYPES.TARGET,
        farmName: FarmName?.BrazilCoffeeFarm || "Brazil Coffee Farm",
        verificationStatus: VERIFICATION_STATUS.FAILED,
        githubLink: `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.brazilFarm}`,
        agentDirectoryLink: `${urlsConfig.agentDirectory.baseUrl}${urlsConfig.agentDirectory.agents.brazilFarm}`,
      },

      position: { x: 232.0903941835277, y: 503.93174725714437 },
    },
    {
      id: NODE_IDS.COLOMBIA_FARM,
      type: NODE_TYPES.CUSTOM,
      data: {
        icon: CoffeeBeanIcon,
        label1: "Colombia",
        label2: "Coffee Farm Agent",
        handles: HANDLE_TYPES.ALL,
        farmName: FarmName?.ColombiaCoffeeFarm || "Colombia Coffee Farm",
        verificationStatus: VERIFICATION_STATUS.VERIFIED,
        hasBadgeDetails: true,
        hasPolicyDetails: true,
        githubLink: `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.colombiaFarm}`,
        agentDirectoryLink: `${urlsConfig.agentDirectory.baseUrl}${urlsConfig.agentDirectory.agents.colombiaFarm}`,
      },
      position: { x: 521.266082170288, y: 505.38817113883306 },
    },
    {
      id: NODE_IDS.VIETNAM_FARM,
      type: NODE_TYPES.CUSTOM,
      data: {
        icon: CoffeeBeanIcon,
        label1: "Vietnam",
        label2: "Coffee Farm Agent",
        handles: HANDLE_TYPES.TARGET,
        farmName: FarmName?.VietnamCoffeeFarm || "Vietnam Coffee Farm",
        verificationStatus: VERIFICATION_STATUS.VERIFIED,
        hasBadgeDetails: true,
        hasPolicyDetails: false,
        githubLink: `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.vietnamFarm}`,
        agentDirectoryLink: `${urlsConfig.agentDirectory.baseUrl}${urlsConfig.agentDirectory.agents.vietnamFarm}`,
      },
      position: { x: 832.9824511707582, y: 505.08339631990395 },
    },
    {
      id: NODE_IDS.WEATHER_MCP,
      type: NODE_TYPES.CUSTOM,
      data: {
        icon: <TiWeatherCloudy className="dark-icon h-4 w-4" />,
        label1: "MCP Server",
        label2: "Weather",
        handles: HANDLE_TYPES.TARGET,
        githubLink: `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.weatherMcp}`,
        agentDirectoryLink: `${urlsConfig.agentDirectory.baseUrl}${urlsConfig.agentDirectory.agents.weatherMcp}`,
      },
      position: { x: 371.266082170288, y: 731.9104402412228 },
    },
    {
      id: NODE_IDS.PAYMENT_MCP,
      type: NODE_TYPES.CUSTOM,
      data: {
        icon: <Calculator className="dark-icon h-4 w-4" />,
        label1: "MCP Server",
        label2: "Payment",
        handles: HANDLE_TYPES.TARGET,
        verificationStatus: VERIFICATION_STATUS.VERIFIED,
        hasBadgeDetails: true,
        hasPolicyDetails: false,
        githubLink: `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.paymentMcp}`,
        agentDirectoryLink: urlsConfig.agentDirectory.baseUrl,
      },
      position: { x: 671.266082170288, y: 731.9104402412228 },
    },
  ],
  edges: [
    {
      id: EDGE_IDS.AUCTION_TO_TRANSPORT,
      source: NODE_IDS.AUCTION_AGENT,
      target: NODE_IDS.TRANSPORT,
      targetHandle: "top",
      data: { label: EDGE_LABELS.A2A },
      type: EDGE_TYPES.CUSTOM,
    },
    {
      id: EDGE_IDS.TRANSPORT_TO_BRAZIL,
      source: NODE_IDS.TRANSPORT,
      target: NODE_IDS.BRAZIL_FARM,
      sourceHandle: "bottom_left",
      data: { label: EDGE_LABELS.A2A },
      type: EDGE_TYPES.CUSTOM,
    },
    {
      id: EDGE_IDS.TRANSPORT_TO_COLOMBIA,
      source: NODE_IDS.TRANSPORT,
      target: NODE_IDS.COLOMBIA_FARM,
      sourceHandle: "bottom_center",
      data: { label: EDGE_LABELS.A2A },
      type: EDGE_TYPES.CUSTOM,
    },
    {
      id: EDGE_IDS.TRANSPORT_TO_VIETNAM,
      source: NODE_IDS.TRANSPORT,
      target: NODE_IDS.VIETNAM_FARM,
      sourceHandle: "bottom_right",
      data: { label: EDGE_LABELS.A2A },
      type: EDGE_TYPES.CUSTOM,
    },
    {
      id: EDGE_IDS.COLOMBIA_TO_MCP,
      source: NODE_IDS.COLOMBIA_FARM,
      target: NODE_IDS.WEATHER_MCP,
      data: {
        label: EDGE_LABELS.MCP,
        branches: [NODE_IDS.WEATHER_MCP, NODE_IDS.PAYMENT_MCP],
      },
      type: EDGE_TYPES.BRANCHING,
    },
  ],
  animationSequence: [
    { ids: [NODE_IDS.AUCTION_AGENT] },
    { ids: [EDGE_IDS.AUCTION_TO_TRANSPORT] },
    { ids: [NODE_IDS.TRANSPORT] },
    {
      ids: [
        EDGE_IDS.TRANSPORT_TO_BRAZIL,
        EDGE_IDS.TRANSPORT_TO_COLOMBIA,
        EDGE_IDS.TRANSPORT_TO_VIETNAM,
      ],
    },
    {
      ids: [
        NODE_IDS.BRAZIL_FARM,
        NODE_IDS.COLOMBIA_FARM,
        NODE_IDS.VIETNAM_FARM,
      ],
    },
    { ids: [EDGE_IDS.COLOMBIA_TO_MCP] },
    { ids: [NODE_IDS.WEATHER_MCP, NODE_IDS.PAYMENT_MCP] },
  ],
}

const GROUP_COMMUNICATION_CONFIG: GraphConfig = {
  title: "Secure Group Communication Logistics Network",
  nodes: [
    {
      id: NODE_IDS.LOGISTICS_GROUP,
      type: NODE_TYPES.GROUP,
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
      id: NODE_IDS.AUCTION_AGENT,
      type: NODE_TYPES.CUSTOM,
      data: {
        icon: (
          <img
            src={supervisorIcon}
            alt="Supervisor Icon"
            className="dark-icon h-4 w-4 object-contain"
          />
        ),
        label1: "Buyer",
        label2: "Logistics Agent",
        handles: HANDLE_TYPES.SOURCE,
        githubLink: `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.logisticSupervisor}`,
        agentDirectoryLink: urlsConfig.agentDirectory.baseUrl,
      },
      position: { x: 150, y: 100 },
      parentId: NODE_IDS.LOGISTICS_GROUP,
      extent: "parent",
    },
    {
      id: NODE_IDS.TRANSPORT,
      type: NODE_TYPES.TRANSPORT,
      data: {
        label: "Transport: SLIM",
        compact: true,
        githubLink: `${urlsConfig.github.appSdkBaseUrl}${urlsConfig.github.transports.group}`,
      },
      position: { x: 380, y: 270 },
      parentId: NODE_IDS.LOGISTICS_GROUP,
      extent: "parent",
    },
    {
      id: NODE_IDS.BRAZIL_FARM,
      type: NODE_TYPES.CUSTOM,
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
        handles: HANDLE_TYPES.ALL,
        farmName: "Tatooine Farm",
        githubLink: `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.logisticFarm}`,
        agentDirectoryLink: `${urlsConfig.agentDirectory.baseUrl}/`,
      },
      position: { x: 550, y: 100 },
      parentId: NODE_IDS.LOGISTICS_GROUP,
      extent: "parent",
    },
    {
      id: NODE_IDS.COLOMBIA_FARM,
      type: NODE_TYPES.CUSTOM,
      data: {
        icon: (
          <Truck className="dark-icon h-4 w-4 object-contain opacity-100" />
        ),
        label1: "Shipper",
        label2: "Shipper Agent",
        handles: HANDLE_TYPES.TARGET,
        agentName: "Shipper Logistics",
        githubLink: `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.logisticShipper}`,
        agentDirectoryLink: `${urlsConfig.agentDirectory.baseUrl}/`,
      },
      position: { x: 150, y: 500 },
      parentId: NODE_IDS.LOGISTICS_GROUP,
      extent: "parent",
    },
    {
      id: NODE_IDS.VIETNAM_FARM,
      type: NODE_TYPES.CUSTOM,
      data: {
        icon: (
          <Calculator className="dark-icon h-4 w-4 object-contain opacity-100" />
        ),
        label1: "Accountant",
        label2: "Accountant Agent",
        handles: HANDLE_TYPES.TARGET,
        agentName: "Accountant Logistics",
        githubLink: `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.logisticAccountant}`,
        agentDirectoryLink: `${urlsConfig.agentDirectory.baseUrl}/`,
      },
      position: { x: 500, y: 500 },
      parentId: NODE_IDS.LOGISTICS_GROUP,
      extent: "parent",
    },
  ],
  edges: [
    {
      id: EDGE_IDS.SUPERVISOR_TO_TRANSPORT,
      source: NODE_IDS.AUCTION_AGENT,
      target: NODE_IDS.TRANSPORT,
      targetHandle: "top_left",
      data: { label: EDGE_LABELS.A2A },
      type: EDGE_TYPES.CUSTOM,
    },
    {
      id: EDGE_IDS.FARM_TO_TRANSPORT,
      source: NODE_IDS.BRAZIL_FARM,
      target: NODE_IDS.TRANSPORT,
      sourceHandle: "source",
      targetHandle: "top_right",
      data: { label: EDGE_LABELS.A2A },
      type: EDGE_TYPES.CUSTOM,
    },
    {
      id: EDGE_IDS.TRANSPORT_TO_SHIPPER,
      source: NODE_IDS.TRANSPORT,
      target: NODE_IDS.COLOMBIA_FARM,
      sourceHandle: "bottom_left",
      data: { label: EDGE_LABELS.A2A },
      type: EDGE_TYPES.CUSTOM,
    },
    {
      id: EDGE_IDS.TRANSPORT_TO_ACCOUNTANT,
      source: NODE_IDS.TRANSPORT,
      target: NODE_IDS.VIETNAM_FARM,
      sourceHandle: "bottom_right",
      data: { label: EDGE_LABELS.A2A },
      type: EDGE_TYPES.CUSTOM,
    },
  ],
  animationSequence: [
    { ids: [NODE_IDS.AUCTION_AGENT] },
    { ids: [EDGE_IDS.SUPERVISOR_TO_TRANSPORT] },
    { ids: [NODE_IDS.TRANSPORT] },
    {
      ids: [
        EDGE_IDS.FARM_TO_TRANSPORT,
        EDGE_IDS.TRANSPORT_TO_SHIPPER,
        EDGE_IDS.TRANSPORT_TO_ACCOUNTANT,
        NODE_IDS.BRAZIL_FARM,
        NODE_IDS.COLOMBIA_FARM,
        NODE_IDS.VIETNAM_FARM,
      ],
    },
    { ids: [NODE_IDS.BRAZIL_FARM] },
    { ids: [NODE_IDS.COLOMBIA_FARM] },
    { ids: [NODE_IDS.VIETNAM_FARM] },
    { ids: [NODE_IDS.COLOMBIA_FARM] },
  ],
}

export const getGraphConfig = (
  pattern: string,
  _isConnected?: boolean,
): GraphConfig => {
  switch (pattern) {
    case "publish_subscribe":
      return {
        ...PUBLISH_SUBSCRIBE_CONFIG,
        nodes: [...PUBLISH_SUBSCRIBE_CONFIG.nodes],
        edges: [...PUBLISH_SUBSCRIBE_CONFIG.edges],
      }
    case "publish_subscribe_streaming": {
      const streamingConfig = {
        ...PUBLISH_SUBSCRIBE_CONFIG,
        nodes: PUBLISH_SUBSCRIBE_CONFIG.nodes.map((node) => {
          if (node.id === NODE_IDS.AUCTION_AGENT) {
            return {
              ...node,
              data: {
                ...node.data,
                githubLink: `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.supervisorAuctionStreaming}`,
              },
            }
          } else if (node.id === NODE_IDS.BRAZIL_FARM) {
            return {
              ...node,
              data: {
                ...node.data,
                githubLink: `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.brazilFarmStreaming}`,
              },
            }
          } else if (node.id === NODE_IDS.COLOMBIA_FARM) {
            return {
              ...node,
              data: {
                ...node.data,
                githubLink: `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.colombiaFarmStreaming}`,
              },
            }
          } else if (node.id === NODE_IDS.VIETNAM_FARM) {
            return {
              ...node,
              data: {
                ...node.data,
                githubLink: `${urlsConfig.github.baseUrl}${urlsConfig.github.agents.vietnamFarmStreaming}`,
              },
            }
          }
          return node
        }),
        edges: [...PUBLISH_SUBSCRIBE_CONFIG.edges],
      }
      return streamingConfig
    }
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
  isStreaming?: boolean,
): Promise<void> => {
  if (isGroupCommunication(pattern)) {
    return
  }

  try {
    const response = await fetch(
      `${getApiUrlForPattern(pattern)}/transport/config`,
    )
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    const data = await response.json()
    const transport = data.transport

    const transportUrls = isStreaming
      ? urlsConfig.github.transports.streaming
      : urlsConfig.github.transports.regular

    setNodes((nodes: any[]) =>
      nodes.map((node: any) =>
        node.id === NODE_IDS.TRANSPORT
          ? {
              ...node,
              data: {
                ...node.data,
                label: `Transport: ${transport}`,
                githubLink:
                  transport === "SLIM"
                    ? `${urlsConfig.github.appSdkBaseUrl}${transportUrls.slim}`
                    : transport === "NATS"
                      ? `${urlsConfig.github.appSdkBaseUrl}${transportUrls.nats}`
                      : `${urlsConfig.github.appSdkBaseUrl}${urlsConfig.github.transports.general}`,
              },
            }
          : node,
      ),
    )

    setEdges((edges: any[]) =>
      edges.map((edge: any) => {
        if (edge.id === EDGE_IDS.COLOMBIA_TO_MCP) {
          return {
            ...edge,
            data: { ...edge.data, label: `${EDGE_LABELS.MCP}${transport}` },
          }
        }
        return edge
      }),
    )
  } catch (error) {
    logger.apiError("/transport/config", error)
  }
}
