/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { EventV1Wire, TopologyWire } from "@/api/agenticWorkflowsTypes"
import type { Edge, Node } from "@xyflow/react"
import {
  extractStableAgentId,
  transportCanonicalRfId,
} from "@/utils/topologyToReactFlow"

export interface MessagingHighlightIds {
  nodeIds: ReadonlySet<string>
  edgeIds: ReadonlySet<string>
}

/** Read the workflow-instance topology fragment carried on an event_v1. */
export function extractInstanceTopologyFromEvent(
  ev: EventV1Wire,
  workflowName: string,
  instanceId: string,
): TopologyWire | null {
  const inst = ev.data?.workflows?.[workflowName]?.instances?.[instanceId]
  if (!inst || typeof inst !== "object") return null
  const topo = (inst as { topology?: unknown }).topology
  if (!topo || typeof topo !== "object") return null
  return topo as TopologyWire
}

/** Treat every id listed in the partial topology as part of the current
 *  messaging path. Node ids mirror ``rfIdOf`` in topologyToReactFlow:
 *  stable_agent_id for agents, transport canonical id for transports, wire id otherwise. */
export function messagingHighlightIdsFromTopology(
  topology: TopologyWire | null | undefined,
): MessagingHighlightIds {
  const nodeIds = new Set<string>()
  const edgeIds = new Set<string>()
  for (const n of topology?.nodes ?? []) {
    const wireId = (n as { id?: unknown }).id
    const nType = (n as { type?: unknown }).type
    const nLabel = (n as { label?: unknown }).label
    const sid = extractStableAgentId(n as never)
    if (sid) {
      nodeIds.add(sid)
    } else if (nType === "transportNode") {
      nodeIds.add(
        transportCanonicalRfId(typeof nLabel === "string" ? nLabel : undefined),
      )
    } else if (typeof wireId === "string" && wireId.length) {
      nodeIds.add(wireId)
    }
  }
  for (const e of topology?.edges ?? []) {
    const id = (e as { id?: unknown }).id
    if (typeof id === "string" && id.length) edgeIds.add(id)
  }
  return { nodeIds, edgeIds }
}

export function patchGraphActiveHighlight(
  nodes: Node[],
  edges: Edge[],
  highlight: MessagingHighlightIds,
): { nodes: Node[]; edges: Edge[] } {
  const nextNodes = nodes.map((node) => {
    const on = highlight.nodeIds.has(node.id)
    const prev = Boolean(
      (node.data as { active?: unknown } | undefined)?.active,
    )
    if (prev === on) return node
    return {
      ...node,
      data: { ...node.data, active: on },
    }
  })
  const nextEdges = edges.map((edge) => {
    const on = highlight.edgeIds.has(edge.id)
    const prev = Boolean(
      (edge.data as { active?: unknown } | undefined)?.active,
    )
    if (prev === on) return edge
    return {
      ...edge,
      data: { ...edge.data, active: on },
    }
  })
  return { nodes: nextNodes, edges: nextEdges }
}
