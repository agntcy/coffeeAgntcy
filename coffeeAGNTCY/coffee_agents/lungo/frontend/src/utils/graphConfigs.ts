/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { Node, Edge } from "@xyflow/react"
import { NODE_IDS, EDGE_IDS, EDGE_LABELS } from "./const"
import { logger } from "./logger"
import { joinBaseUrl, LUNGO_FRONTEND_URLS } from "@/urls"
import { isGroupCommunication, getApiUrlForPattern } from "./patternUtils"
import {
  type GraphConfig,
  PUBLISH_SUBSCRIBE_CONFIG,
  GROUP_MESSAGING_CONFIG,
  A2A_HTTP_CONFIG,
} from "./graphConfigsData"

export type { GraphConfig }
export { PUBLISH_SUBSCRIBE_CONFIG, GROUP_MESSAGING_CONFIG, A2A_HTTP_CONFIG }

export const getGraphConfig = (pattern: string): GraphConfig => {
  switch (pattern) {
    case "publish_subscribe":
      return {
        ...PUBLISH_SUBSCRIBE_CONFIG,
        nodes: [...PUBLISH_SUBSCRIBE_CONFIG.nodes],
        edges: [...PUBLISH_SUBSCRIBE_CONFIG.edges],
      }
    case "publish_subscribe_streaming": {
      return {
        ...PUBLISH_SUBSCRIBE_CONFIG,
        nodes: PUBLISH_SUBSCRIBE_CONFIG.nodes.map((node) => {
          if (node.id === NODE_IDS.AUCTION_AGENT) {
            return {
              ...node,
              data: {
                ...node.data,
                githubLink: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.supervisorAuctionStreaming}`,
              },
            }
          }
          if (node.id === NODE_IDS.BRAZIL_FARM) {
            return {
              ...node,
              data: {
                ...node.data,
                githubLink: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.brazilFarmStreaming}`,
              },
            }
          }
          if (node.id === NODE_IDS.COLOMBIA_FARM) {
            return {
              ...node,
              data: {
                ...node.data,
                githubLink: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.colombiaFarmStreaming}`,
              },
            }
          }
          if (node.id === NODE_IDS.VIETNAM_FARM) {
            return {
              ...node,
              data: {
                ...node.data,
                githubLink: `${LUNGO_FRONTEND_URLS.github.baseUrl}${LUNGO_FRONTEND_URLS.github.agents.vietnamFarmStreaming}`,
              },
            }
          }
          return node
        }),
        edges: [...PUBLISH_SUBSCRIBE_CONFIG.edges],
      }
    }
    case "group_messaging":
      return GROUP_MESSAGING_CONFIG
    case "a2a_http":
      return A2A_HTTP_CONFIG
    default:
      return PUBLISH_SUBSCRIBE_CONFIG
  }
}

export const updateTransportLabels = async (
  setNodes: (updater: (nodes: Node[]) => Node[]) => void,
  setEdges: (updater: (edges: Edge[]) => Edge[]) => void,
  pattern?: string,
  isStreaming?: boolean,
): Promise<void> => {
  if (isGroupCommunication(pattern)) {
    return
  }

  try {
    const response = await fetch(
      joinBaseUrl(
        getApiUrlForPattern(pattern),
        LUNGO_FRONTEND_URLS.apiPaths.transportConfig,
      ),
    )
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    const data = await response.json()
    const transport = data.transport

    const transportUrls = isStreaming
      ? LUNGO_FRONTEND_URLS.github.transports.streaming
      : LUNGO_FRONTEND_URLS.github.transports.regular

    setNodes((nodes: Node[]) =>
      nodes.map((node: Node) =>
        node.id === NODE_IDS.TRANSPORT
          ? {
              ...node,
              data: {
                ...node.data,
                label: `Transport: ${transport}`,
                githubLink:
                  transport === "SLIM"
                    ? `${LUNGO_FRONTEND_URLS.github.appSdkBaseUrl}${transportUrls.slim}`
                    : transport === "NATS"
                      ? `${LUNGO_FRONTEND_URLS.github.appSdkBaseUrl}${transportUrls.nats}`
                      : `${LUNGO_FRONTEND_URLS.github.appSdkBaseUrl}${LUNGO_FRONTEND_URLS.github.transports.general}`,
              },
            }
          : node,
      ),
    )

    setEdges((edges: Edge[]) =>
      edges.map((edge: Edge) => {
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
    logger.apiError(LUNGO_FRONTEND_URLS.apiPaths.transportConfig, error)
  }
}
