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
import type { StaticIdMap } from "@/utils/topologyStaticIdMap"
import { parseStableAgentUuid } from "@/utils/agenticTopologyIdentityUiMap"

export interface MessagingHighlightIds {
  nodeIds: ReadonlySet<string>
  edgeIds: ReadonlySet<string>
  /** rfId source->target pairs derived from partial topology, used as a
   *  fallback when allocator-minted edge ids drift between event and
   *  refetched topology. */
  edgePairs: ReadonlySet<string>
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
  const edgePairs = new Set<string>()
  // wire id -> rf id, so edges can be translated to node-id pairs
  const wireToRf = new Map<string, string>()
  for (const n of topology?.nodes ?? []) {
    const wireId = (n as { id?: unknown }).id
    const nType = (n as { type?: unknown }).type
    const nLabel = (n as { label?: unknown }).label
    const sid = extractStableAgentId(n as never)
    let rfId: string | null = null
    if (sid) {
      rfId = sid
    } else if (nType === "transportNode") {
      rfId = transportCanonicalRfId(
        typeof nLabel === "string" ? nLabel : undefined,
      )
    } else if (typeof wireId === "string" && wireId.length) {
      rfId = wireId
    }
    if (rfId) {
      nodeIds.add(rfId)
      if (typeof wireId === "string" && wireId.length) {
        wireToRf.set(wireId, rfId)
      }
    }
  }
  for (const e of topology?.edges ?? []) {
    const id = (e as { id?: unknown }).id
    if (typeof id === "string" && id.length) edgeIds.add(id)
    const src = (e as { source?: unknown }).source
    const tgt = (e as { target?: unknown }).target
    if (typeof src === "string" && typeof tgt === "string") {
      const s = wireToRf.get(src) ?? src
      const t = wireToRf.get(tgt) ?? tgt
      edgePairs.add(`${s}->${t}`)
    }
  }
  return { nodeIds, edgeIds, edgePairs }
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
      highlight.edgePairs.has(`${edge.source}->${edge.target}`)
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
 * Like `messagingHighlightIdsFromTopology`, but additionally consults wire
 * labels via the supplied id map's `idByLabel`. Labels are the only way to
 * bridge nodes that don't carry a stable_agent_id (e.g. the Logistics Group
 * container, the AGNTCY Agent Directory node).
 *
 * Falls back to dynamic id form when no static id match is found, so the
 * patch step simply skips ids without a static counterpart.
 */
export function highlightIdsFromTopologyWithOverlay(
  topology: TopologyWire | null | undefined,
  idMap: StaticIdMap,
): MessagingHighlightIds {
  const nodeIds = new Set<string>()
  const edgeIds = new Set<string>()
  const edgePairs = new Set<string>()
  const wireToRf = new Map<string, string>()
  for (const n of topology?.nodes ?? []) {
    const wireId = (n as { id?: unknown }).id
    const nType = (n as { type?: unknown }).type
    const nLabel = (n as { label?: unknown }).label
    const labelStr = typeof nLabel === "string" ? nLabel : ""
    const sid = extractStableAgentId(n as never)
    let rfId: string | null = null
    // 1. stable_agent_id -> static
    if (sid) {
      const uuid = parseStableAgentUuid(sid)
      if (uuid) {
        const viaStable = idMap.idByStableAgentUuid.get(uuid)
        if (viaStable !== undefined) rfId = viaStable
      }
      if (rfId === null) rfId = sid // pass through; patch step will skip unmatched
    }
    // 2. transport canonical -> static
    if (rfId === null && nType === "transportNode") {
      const canon = transportCanonicalRfId(labelStr || undefined)
      const key = canon.replace(/^transport:\/\//, "")
      const viaTransport = idMap.idByTransportKey.get(key)
      rfId = viaTransport !== undefined ? viaTransport : canon
    }
    // 3. label -> static (covers logistics-group, agntcy-directory)
    if (rfId === null && labelStr) {
      const viaLabel = idMap.idByLabel.get(labelStr.trim().toLowerCase())
      if (viaLabel !== undefined) rfId = viaLabel
    }
    // 4. wire id fallback
    if (rfId === null && typeof wireId === "string" && wireId.length) {
      rfId = wireId
    }
    if (rfId) {
      nodeIds.add(rfId)
      if (typeof wireId === "string" && wireId.length) {
        wireToRf.set(wireId, rfId)
      }
    }
  }
  for (const e of topology?.edges ?? []) {
    const id = (e as { id?: unknown }).id
    if (typeof id === "string" && id.length) edgeIds.add(id)
    const src = (e as { source?: unknown }).source
    const tgt = (e as { target?: unknown }).target
    if (typeof src === "string" && typeof tgt === "string") {
      const s = wireToRf.get(src) ?? src
      const t = wireToRf.get(tgt) ?? tgt
      edgePairs.add(`${s}->${t}`)
    }
  }
  return { nodeIds, edgeIds, edgePairs }
}
