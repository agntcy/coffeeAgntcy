/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { Node } from "@xyflow/react"
import type { GraphConfig } from "@/utils/graphConfigs"

/**
 * Minimal node data shape used for sender→node mapping and agent node filtering.
 * GraphConfig.nodes is heterogeneous (CustomNodeData | TransportNodeData | group data);
 * we only read these optional fields, which exist on custom nodes and are absent on
 * transport/group nodes. See @/components/MainArea/Graph/Elements/types (CustomNodeData)
 * for the full custom-node shape.
 * Index signature satisfies @xyflow/react Node<T> constraint (T extends Record<string, unknown>).
 */
export interface GroupCommNodeDataForMapping extends Record<string, unknown> {
  label1?: string
  label2?: string
  agentName?: string
  farmName?: string
}

export function buildSenderToNodeMap(
  graphConfig: GraphConfig | undefined,
): Record<string, string> {
  const map: Record<string, string> = {}

  if (!graphConfig?.nodes) return map

  graphConfig.nodes.forEach((node: Node<GroupCommNodeDataForMapping>) => {
    const data = node.data
    if (data) {
      if (data.label1) {
        map[data.label1] = node.id
        map[data.label1.toLowerCase()] = node.id
      }
      if (data.label2) {
        map[data.label2] = node.id
        map[data.label2.toLowerCase()] = node.id
      }
      if (data.agentName) {
        map[data.agentName] = node.id
        map[data.agentName.toLowerCase()] = node.id
      }
      if (data.farmName) {
        map[data.farmName] = node.id
        map[data.farmName.toLowerCase()] = node.id
      }

      if (data.label1 === "Buyer") {
        map["Supervisor"] = node.id
        map["supervisor"] = node.id
      }
      if (data.label1 === "Tatooine") {
        map["Tatooine Farm"] = node.id
        map["tatooine farm"] = node.id
      }
    }
  })

  return map
}

export function getAllAgentNodeIds(
  graphConfig: GraphConfig | undefined,
): string[] {
  if (!graphConfig?.nodes) return []

  return graphConfig.nodes
    .filter(
      (node: Node<GroupCommNodeDataForMapping>) =>
        node.type === "customNode" && node.data?.label1 !== "Logistics Agent",
    )
    .map((node) => node.id)
}

export function formatAgentName(agentName: string): string {
  if (agentName === "Supervisor") {
    return "Buyer"
  }
  if (agentName === "Tatooine Farm") {
    return "Tatooine"
  }

  return agentName
}
