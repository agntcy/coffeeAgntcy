/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import Air from "@mui/icons-material/Air"
import Calculate from "@mui/icons-material/Calculate"
import LocalShipping from "@mui/icons-material/LocalShipping"
import { Node, Edge } from "@xyflow/react"
import { GraphDiscoveryAssetImg } from "@/utils/GraphDiscoveryAssetImg"
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
import { LUNGO_FRONTEND_URLS } from "@/urls"

function graphNodeIconImg(
  src: string,
  alt: string,
  options?: { invertInDarkMode?: boolean },
) {
  return (
    <GraphDiscoveryAssetImg
      src={src}
      alt={alt}
      invertInDarkMode={options?.invertInDarkMode}
    />
  )
}

export interface GraphConfig {
  title: string
  nodes: Node[]
  edges: Edge[]
  animationSequence: { ids: string[] }[]
}

const SupervisorIcon = graphNodeIconImg(supervisorIcon, "Supervisor Icon", {
  invertInDarkMode: true,
})
const CoffeeBeanIcon = graphNodeIconImg(
  farmAgentIcon,
  "Coffee Farm Agent Icon",
  {
    invertInDarkMode: true,
  },
)
const FarmAgentIcon = graphNodeIconImg(farmAgentIcon, "Farm Agent Icon", {
  invertInDarkMode: true,
})

export const PUBLISH_SUBSCRIBE_CONFIG: GraphConfig = {
  title: "Publish Subscribe",
  nodes: [
    {
      id: NODE_IDS.AUCTION_AGENT,
      type: NODE_TYPES.CUSTOM,
      data: {
        icon: SupervisorIcon,
        label1: "Auction Agent",
        label2: "Buyer",
        handles: HANDLE_TYPES.SOURCE,
        verificationStatus: VERIFICATION_STATUS.VERIFIED,
        hasBadgeDetails: true,
        hasPolicyDetails: true,
        githubLink: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.supervisorAuction}`,
        agentDirectoryLink: `${LUNGO_FRONTEND_URLS.agentDirectory.baseUrl}${LUNGO_FRONTEND_URLS.agentDirectory.agents.supervisorAuction}`,
      },
      position: { x: 527.1332569384248, y: 76.4805787605829 },
    },
    {
      id: NODE_IDS.TRANSPORT,
      type: NODE_TYPES.TRANSPORT,
      data: {
        label: "Transport: ",
        githubLink: `${LUNGO_FRONTEND_URLS.github.appSdkBaseUrl}${LUNGO_FRONTEND_URLS.github.transports.general}`,
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
        githubLink: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.brazilFarm}`,
        agentDirectoryLink: `${LUNGO_FRONTEND_URLS.agentDirectory.baseUrl}${LUNGO_FRONTEND_URLS.agentDirectory.agents.brazilFarm}`,
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
        githubLink: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.colombiaFarm}`,
        agentDirectoryLink: `${LUNGO_FRONTEND_URLS.agentDirectory.baseUrl}${LUNGO_FRONTEND_URLS.agentDirectory.agents.colombiaFarm}`,
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
        githubLink: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.vietnamFarm}`,
        agentDirectoryLink: `${LUNGO_FRONTEND_URLS.agentDirectory.baseUrl}${LUNGO_FRONTEND_URLS.agentDirectory.agents.vietnamFarm}`,
      },
      position: { x: 832.9824511707582, y: 505.08339631990395 },
    },
    {
      id: NODE_IDS.WEATHER_MCP,
      type: NODE_TYPES.CUSTOM,
      data: {
        icon: <Air />,
        label1: "Weather",
        label2: "MCP Server",
        directoryAgentSlug: "weather-mcp-server",
        handles: HANDLE_TYPES.TARGET,
        githubLink: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.weatherMcp}`,
        agentDirectoryLink: `${LUNGO_FRONTEND_URLS.agentDirectory.baseUrl}${LUNGO_FRONTEND_URLS.agentDirectory.agents.weatherMcp}`,
      },
      position: { x: 371.266082170288, y: 731.9104402412228 },
    },
    {
      id: NODE_IDS.PAYMENT_MCP,
      type: NODE_TYPES.CUSTOM,
      data: {
        icon: <Calculate />,
        label1: "Payment",
        label2: "MCP Server",
        directoryAgentSlug: "payment-mcp-server",
        handles: HANDLE_TYPES.TARGET,
        verificationStatus: VERIFICATION_STATUS.VERIFIED,
        hasBadgeDetails: true,
        hasPolicyDetails: false,
        githubLink: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.paymentMcp}`,
        agentDirectoryLink: LUNGO_FRONTEND_URLS.agentDirectory.baseUrl,
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

export const GROUP_MESSAGING_CONFIG: GraphConfig = {
  title: "Group Messaging",
  nodes: [
    {
      id: NODE_IDS.LOGISTICS_GROUP,
      type: NODE_TYPES.GROUP,
      data: {},
      position: { x: 50, y: 50 },
      hidden: true,
      width: 900,
      height: 650,
    },
    {
      id: NODE_IDS.AUCTION_AGENT,
      type: NODE_TYPES.CUSTOM,
      data: {
        icon: SupervisorIcon,
        label1: "Buyer",
        label2: "Logistics Agent",
        handles: HANDLE_TYPES.SOURCE,
        githubLink: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.logisticSupervisor}`,
        agentDirectoryLink: LUNGO_FRONTEND_URLS.agentDirectory.baseUrl,
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
        githubLink: `${LUNGO_FRONTEND_URLS.github.appSdkBaseUrl}${LUNGO_FRONTEND_URLS.github.transports.group}`,
      },
      position: { x: 380, y: 270 },
      parentId: NODE_IDS.LOGISTICS_GROUP,
      extent: "parent",
    },
    {
      id: NODE_IDS.BRAZIL_FARM,
      type: NODE_TYPES.CUSTOM,
      data: {
        icon: FarmAgentIcon,
        label1: "Tatooine",
        label2: "Coffee Farm Agent",
        handles: HANDLE_TYPES.ALL,
        farmName: "Tatooine Farm",
        githubLink: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.logisticFarm}`,
        agentDirectoryLink: `${LUNGO_FRONTEND_URLS.agentDirectory.baseUrl}/`,
      },
      position: { x: 550, y: 100 },
      parentId: NODE_IDS.LOGISTICS_GROUP,
      extent: "parent",
    },
    {
      id: NODE_IDS.COLOMBIA_FARM,
      type: NODE_TYPES.CUSTOM,
      data: {
        icon: <LocalShipping />,
        label1: "Shipper",
        label2: "Shipper Agent",
        handles: HANDLE_TYPES.TARGET,
        agentName: "Shipper Logistics",
        githubLink: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.logisticShipper}`,
        agentDirectoryLink: `${LUNGO_FRONTEND_URLS.agentDirectory.baseUrl}/`,
      },
      position: { x: 150, y: 500 },
      parentId: NODE_IDS.LOGISTICS_GROUP,
      extent: "parent",
    },
    {
      id: NODE_IDS.VIETNAM_FARM,
      type: NODE_TYPES.CUSTOM,
      data: {
        icon: <Calculate />,
        label1: "Accountant",
        label2: "Accountant Agent",
        handles: HANDLE_TYPES.TARGET,
        agentName: "Accountant Logistics",
        githubLink: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.logisticAccountant}`,
        agentDirectoryLink: `${LUNGO_FRONTEND_URLS.agentDirectory.baseUrl}/`,
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

export const A2A_HTTP_CONFIG: GraphConfig = {
  title: "A2A HTTP",
  nodes: [
    {
      id: NODE_IDS.RECRUITER,
      type: NODE_TYPES.CUSTOM,
      data: {
        icon: graphNodeIconImg(supervisorIcon, "Recruiter Icon", {
          invertInDarkMode: true,
        }),
        label1: "Agentic Recruiter",
        label2: "Discovery and delegation",
        handles: HANDLE_TYPES.ALL,
        extraHandles: [
          { id: "target-right", type: "target", position: "right" },
        ],
        selected: true,
        verificationStatus: VERIFICATION_STATUS.VERIFIED,
        githubLink: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.recruiter}`,
      },
      position: { x: 400, y: 300 },
    },
    {
      id: NODE_IDS.DIRECTORY,
      type: NODE_TYPES.CUSTOM,
      data: {
        icon: graphNodeIconImg(supervisorIcon, "Directory Icon", {
          invertInDarkMode: true,
        }),
        label1: "Directory",
        label2: "AGNTCY Agent Directory",
        handles: HANDLE_TYPES.ALL,
        extraHandles: [{ id: "source-left", type: "source", position: "left" }],
        githubLink: `${LUNGO_FRONTEND_URLS.agentDirectory.github}`,
        agentDirectoryLink: "place-holder",
      },
      position: { x: 800, y: 100 },
    },
  ],
  edges: [
    {
      id: EDGE_IDS.RECRUITER_TO_DIRECTORY,
      source: NODE_IDS.DIRECTORY,
      target: NODE_IDS.RECRUITER,
      sourceHandle: "source-left",
      targetHandle: "target-right",
      data: { label: EDGE_LABELS.MCP_WITH_STDIO },
      type: EDGE_TYPES.CUSTOM,
    },
  ],
  animationSequence: [
    { ids: [NODE_IDS.RECRUITER] },
    { ids: [EDGE_IDS.RECRUITER_TO_DIRECTORY] },
    { ids: [NODE_IDS.DIRECTORY] },
  ],
}
