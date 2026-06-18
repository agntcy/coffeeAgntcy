/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import LocalShipping from "@mui/icons-material/LocalShipping"
import SmartToy from "@mui/icons-material/SmartToy"
import type { Edge, Node } from "@xyflow/react"
import type {
  TopologyEdgeWire,
  TopologyNodeWire,
  TopologyWire,
} from "@/api/agenticWorkflowsTypes"
import {
  EDGE_LABELS,
  EDGE_TYPES,
  HANDLE_TYPES,
  NODE_TYPES,
  VERIFICATION_STATUS,
} from "@/utils/const"
import type {
  CustomNodeData,
  TransportNodeData,
} from "@/components/MainArea/Graph/Elements/types"
import {
  layoutPositionsByLayer,
  layoutSlimTransportGraph,
} from "@/utils/topologyLayout"
import {
  applyBackendTopologyWireFields,
  directoryAgentSlugFromAgentRecordUri,
  enrichAgenticTopologyWellKnownUi,
  resolveGithubFromAgentRecordUri,
  splitTopologyNodeLabel,
} from "@/utils/agenticTopologyIdentityUiMap"

// Transport label -> canonical synonym. Seed emits "transport"; runtime emits
// "slim"/"nats"/"jsonrpc" for the same logical transport. Distinct logical
// transports must use labels outside this table to avoid collapsing.
const TRANSPORT_SYNONYMS: Record<string, string> = {
  transport: "transport",
  slim: "transport",
  nats: "transport",
  jsonrpc: "transport",
}
const CONCRETE_TRANSPORTS = new Set(
  Object.entries(TRANSPORT_SYNONYMS)
    .filter(([k]) => k !== "transport")
    .map(([k]) => k),
)

function normalizedTransportKey(label: string | undefined): string {
  const lower = typeof label === "string" ? label.trim().toLowerCase() : ""
  return TRANSPORT_SYNONYMS[lower] ?? lower
}

export function transportCanonicalRfId(label: string | undefined): string {
  return `transport://${normalizedTransportKey(label)}`
}

/** Read ``stable_agent_id`` from a wire node, handling both ``string`` and
 * ``{ root: string }`` shapes. Returns "" when absent. */
export function extractStableAgentId(n: TopologyNodeWire): string {
  const s = n.stable_agent_id
  if (typeof s === "string") return s
  if (s && typeof s === "object" && typeof s.root === "string") return s.root
  return ""
}

function defaultCustomIcon(label: string): React.ReactNode {
  const lower = label.toLowerCase()
  if (lower.includes("transport")) {
    return <LocalShipping aria-hidden />
  }
  return <SmartToy aria-hidden />
}

export interface TopologyToFlowOptions {
  /** When false, skip SecurityClass check for tests. */
  validateUrls?: boolean
}

export function topologyWireToReactFlow(
  topology: TopologyWire | undefined | null,
  options: TopologyToFlowOptions = {},
): { nodes: Node[]; edges: Edge[] } {
  const validateUrls = options.validateUrls !== false
  const nodesIn = topology?.nodes ?? []
  const edgesIn = topology?.edges ?? []

  // Collapse trace-minted node://UUID aliases via stable_agent_id; fall back
  // to a (type, label) tuple for seed nodes that lack the field.
  const dedupKeyFor = (n: TopologyNodeWire): string => {
    const sid = extractStableAgentId(n)
    if (sid) return `sid::${sid}`
    const typeKey =
      n.type === NODE_TYPES.TRANSPORT ? NODE_TYPES.TRANSPORT : NODE_TYPES.CUSTOM
    const labelKey =
      typeKey === NODE_TYPES.TRANSPORT
        ? normalizedTransportKey(n.label)
        : typeof n.label === "string"
          ? n.label.trim().toLowerCase()
          : ""
    return `lbl::${typeKey}::${labelKey}`
  }
  const aliasToCanonical = new Map<string, string>()
  const canonicalKeyToId = new Map<string, string>()
  const canonicalIdToNode = new Map<string, TopologyNodeWire>()
  const dedupedNodesIn: TopologyNodeWire[] = []
  for (const n of nodesIn) {
    if (!n?.id) continue
    const dedupKey = dedupKeyFor(n)
    const existing = canonicalKeyToId.get(dedupKey)
    if (existing) {
      aliasToCanonical.set(n.id, existing)
      // Prefer the more-informative label when later events upgrade it
      // (e.g. "Transport" -> "SLIM", "agent" -> "Supervisor agent"). Never
      // downgrade a concrete transport name back to a generic seed label.
      const prev = canonicalIdToNode.get(existing)
      if (prev) {
        const prevLabel = typeof prev.label === "string" ? prev.label : ""
        const nextLabel = typeof n.label === "string" ? n.label : ""
        const prevIsConcreteTransport =
          prev.type === NODE_TYPES.TRANSPORT &&
          CONCRETE_TRANSPORTS.has(prevLabel.trim().toLowerCase())
        const nextIsConcreteTransport =
          n.type === NODE_TYPES.TRANSPORT &&
          CONCRETE_TRANSPORTS.has(nextLabel.trim().toLowerCase())
        if (nextIsConcreteTransport) {
          prev.label = nextLabel
        } else if (
          !prevIsConcreteTransport &&
          nextLabel.length > prevLabel.length
        ) {
          prev.label = nextLabel
        }
        if (!prev.agent_record_uri && n.agent_record_uri) {
          prev.agent_record_uri = n.agent_record_uri
        }
      }
      continue
    }
    canonicalKeyToId.set(dedupKey, n.id)
    aliasToCanonical.set(n.id, n.id)
    // Clone before in-place label/uri upgrades.
    const cloned: TopologyNodeWire = { ...n }
    canonicalIdToNode.set(n.id, cloned)
    dedupedNodesIn.push(cloned)
  }
  const canonical = (id: string | undefined): string =>
    id ? (aliasToCanonical.get(id) ?? id) : ""

  // stable_agent_id for agents, synonym-normalized canonical id for
  // transports, wire id otherwise.
  const rfIdOf = (n: TopologyNodeWire): string => {
    const sid = extractStableAgentId(n)
    if (sid) return sid
    if (n.type === NODE_TYPES.TRANSPORT) {
      return transportCanonicalRfId(n.label)
    }
    return n.id
  }
  const wireIdToRfId = new Map<string, string>()
  for (const n of dedupedNodesIn) {
    wireIdToRfId.set(n.id, rfIdOf(n))
  }
  for (const [alias, can] of aliasToCanonical.entries()) {
    const rf = wireIdToRfId.get(can)
    if (rf) wireIdToRfId.set(alias, rf)
  }
  const rfIdFor = (wireId: string | undefined): string =>
    wireId ? (wireIdToRfId.get(wireId) ?? wireId) : ""

  const layerById = new Map<string, number>()
  for (const n of dedupedNodesIn) {
    const rfId = rfIdOf(n)
    if (rfId) layerById.set(rfId, n.layer_index ?? 0)
  }
  const pos = layoutPositionsByLayer(dedupedNodesIn.map(rfIdOf), layerById)

  const positions = new Map<string, { x: number; y: number }>()
  for (const n of dedupedNodesIn) {
    const rfId = rfIdOf(n)
    const position =
      n.position &&
      typeof n.position.x === "number" &&
      typeof n.position.y === "number"
        ? { x: n.position.x, y: n.position.y }
        : (pos.get(rfId) ?? { x: 0, y: 0 })
    positions.set(rfId, position)
  }

  const nodes: Node[] = dedupedNodesIn.map((n): Node => {
    const rfId = rfIdOf(n)
    const nodeType =
      n.type === NODE_TYPES.TRANSPORT ? NODE_TYPES.TRANSPORT : NODE_TYPES.CUSTOM
    const position = positions.get(rfId) ?? { x: 0, y: 0 }
    const gh = resolveGithubFromAgentRecordUri(
      n.agent_record_uri as string | undefined,
      { validateUrls },
    )

    if (nodeType === NODE_TYPES.TRANSPORT) {
      const data: TransportNodeData = {
        label: typeof n.label === "string" ? n.label : "Transport",
        githubLink: gh,
        compact: false,
      }
      return {
        id: rfId,
        type: NODE_TYPES.TRANSPORT,
        position,
        data: data as unknown as Record<string, unknown>,
      }
    }

    const labelStr = typeof n.label === "string" ? n.label : ""
    const { label1, label2 } = splitTopologyNodeLabel(labelStr)
    const directoryAgentSlug = directoryAgentSlugFromAgentRecordUri(
      n.agent_record_uri as string | undefined,
    )
    let data: CustomNodeData = {
      icon: defaultCustomIcon(labelStr),
      label1,
      label2,
      handles: HANDLE_TYPES.ALL,
      verificationStatus: VERIFICATION_STATUS.VERIFIED,
      githubLink: gh,
      ...(directoryAgentSlug ? { directoryAgentSlug } : {}),
    }
    data = applyBackendTopologyWireFields(data, n, { validateUrls })
    data = enrichAgenticTopologyWellKnownUi(data, n, { validateUrls })

    return {
      id: rfId,
      type: NODE_TYPES.CUSTOM,
      position,
      data: data as unknown as Record<string, unknown>,
    }
  })

  const seenEdgePairs = new Set<string>()
  const edges: Edge[] = []
  for (const raw of edgesIn) {
    const e = raw as TopologyEdgeWire
    const source = rfIdFor(canonical(e.source))
    const target = rfIdFor(canonical(e.target))
    if (!source || !target) continue
    const pairKey = `${source}->${target}`
    if (seenEdgePairs.has(pairKey)) continue
    seenEdgePairs.add(pairKey)
    const edgeType =
      e.type === EDGE_TYPES.BRANCHING ? EDGE_TYPES.BRANCHING : EDGE_TYPES.CUSTOM
    const base: Edge = {
      id: e.id,
      source,
      target,
      type: edgeType,
      data: {
        label:
          typeof e.type === "string" && e.type.toLowerCase().includes("mcp")
            ? EDGE_LABELS.MCP
            : EDGE_LABELS.A2A,
      },
    }
    const branches = (e as { branches?: string[] }).branches
    if (edgeType === EDGE_TYPES.BRANCHING && Array.isArray(branches)) {
      base.data = {
        ...base.data,
        branches,
      }
    }
    edges.push(base)
  }

  return layoutSlimTransportGraph(nodes, edges)
}
