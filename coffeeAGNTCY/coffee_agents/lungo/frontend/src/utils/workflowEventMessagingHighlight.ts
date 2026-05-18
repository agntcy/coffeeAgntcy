/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type {
  EventV1Wire,
  TopologyNodeWire,
  TopologyWire,
} from "@/api/agenticWorkflowsTypes"
import type { Edge, Node } from "@xyflow/react"
import {
  extractStableAgentId,
  transportCanonicalRfId,
} from "@/utils/topologyToReactFlow"
import type { StaticIdMap } from "@/utils/topologyStaticIdMap"
import { parseStableAgentUuid } from "@/utils/agenticTopologyIdentityUiMap"

export interface MessagingHighlightIds {
  nodeIds: ReadonlySet<string>
  edgeIds: ReadonlySet<string>
  /**
   * rfId source->target pairs; fallback for drifted allocator-minted edge ids.
   */
  edgePairs: ReadonlySet<string>
}

type NodeIdResolver = (node: TopologyNodeWire) => string | null

const TRANSPORT_NODE_TYPE = "transportNode"

/**
 * Guard for wire fields that must be non-empty before they can identify graph items.
 */
function hasText(value: unknown): value is string {
  return typeof value === "string" && value.length > 0
}

/** Keep label fallback lookups consistent with the static id maps. */
function normalizedLabel(value: unknown): string {
  return typeof value === "string" ? value.trim().toLowerCase() : ""
}

/**
 * React Flow edge ids can drift, so source/target pairs provide a stable backup key.
 */
function edgePairId(source: string, target: string): string {
  return `${source}->${target}`
}

function emptyMessagingHighlightIds(): MessagingHighlightIds {
  return { nodeIds: new Set(), edgeIds: new Set(), edgePairs: new Set() }
}

/** Match the dynamic ids produced by `topologyWireToReactFlow`. */
function resolveDynamicNodeId(node: TopologyNodeWire): string | null {
  const stableAgentId = extractStableAgentId(node)
  if (stableAgentId) return stableAgentId
  if (node.type === TRANSPORT_NODE_TYPE)
    return transportCanonicalRfId(node.label)
  return hasText(node.id) ? node.id : null
}

/** Translate wire ids into authored static graph ids used by legacy patterns. */
function resolveStaticGraphNodeId(
  node: TopologyNodeWire,
  idMap: StaticIdMap,
): string | null {
  const stableAgentId = extractStableAgentId(node)
  if (stableAgentId) {
    const uuid = parseStableAgentUuid(stableAgentId)
    const staticId = uuid ? idMap.idByStableAgentUuid.get(uuid) : undefined
    return staticId ?? stableAgentId
  }

  if (node.type === TRANSPORT_NODE_TYPE) {
    const canonicalId = transportCanonicalRfId(node.label)
    const transportKey = canonicalId.replace(/^transport:\/\//, "")
    return idMap.idByTransportKey.get(transportKey) ?? canonicalId
  }

  const labelId = idMap.idByLabel.get(normalizedLabel(node.label))
  if (labelId !== undefined) return labelId

  return hasText(node.id) ? node.id : null
}

/** Shared topology traversal; callers only choose how each node id is resolved. */
function collectMessagingHighlightIds(
  topology: TopologyWire | null | undefined,
  resolveNodeId: NodeIdResolver,
): MessagingHighlightIds {
  if (!topology) return emptyMessagingHighlightIds()

  const nodeIds = new Set<string>()
  const edgeIds = new Set<string>()
  const edgePairs = new Set<string>()
  const wireIdToRenderedId = new Map<string, string>()

  for (const node of topology.nodes ?? []) {
    const renderedId = resolveNodeId(node)
    if (!renderedId) continue

    nodeIds.add(renderedId)
    if (hasText(node.id)) wireIdToRenderedId.set(node.id, renderedId)
  }

  for (const edge of topology.edges ?? []) {
    if (hasText(edge.id)) edgeIds.add(edge.id)
    if (!hasText(edge.source) || !hasText(edge.target)) continue

    const source = wireIdToRenderedId.get(edge.source) ?? edge.source
    const target = wireIdToRenderedId.get(edge.target) ?? edge.target
    edgePairs.add(edgePairId(source, target))
  }

  return { nodeIds, edgeIds, edgePairs }
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

/** Build highlight ids in the dynamic React Flow id namespace. */
export function messagingHighlightIdsFromTopology(
  topology: TopologyWire | null | undefined,
): MessagingHighlightIds {
  return collectMessagingHighlightIds(topology, resolveDynamicNodeId)
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
    const on =
      highlight.edgeIds.has(edge.id) ||
      highlight.edgePairs.has(edgePairId(edge.source, edge.target))
    const prev = Boolean(
      (edge.data as { active?: unknown } | undefined)?.active,
    )
    if (prev === on && Boolean(edge.animated) === on) return edge
    return {
      ...edge,
      animated: on,
      data: { ...edge.data, active: on },
    }
  })
  return { nodes: nextNodes, edges: nextEdges }
}

/**
 * Build highlight ids in the static graph id namespace when a pattern uses authored nodes.
 */
export function staticGraphHighlightIdsFromTopology(
  topology: TopologyWire | null | undefined,
  idMap: StaticIdMap,
): MessagingHighlightIds {
  return collectMessagingHighlightIds(topology, (node) =>
    resolveStaticGraphNodeId(node, idMap),
  )
}
