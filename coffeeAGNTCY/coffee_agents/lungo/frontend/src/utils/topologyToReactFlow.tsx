/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

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
  ExtraHandle,
  TransportNodeData,
} from "@/components/MainArea/Graph/Elements/types"
import {
  layoutPositionsByLayer,
  layoutSlimTransportGraph,
} from "@/utils/topologyLayout"
import {
  enrichAgenticTopologyWellKnownUi,
  isDirectoryLabel,
  isMcpServerLabel,
  isRecruiterLabel,
  mergeAgenticTopologyIdentityUi,
  resolveGithubFromAgentRecordUri,
  splitTopologyNodeLabel,
} from "@/utils/agenticTopologyIdentityUiMap"
import type { IdentityUiGithubVariant } from "@/utils/agenticTopologyIdentityUiMap"
import { resolveTopologyNodeIcon } from "@/utils/topologyNodeIcons"

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

// Group container defaults; the compact-group layout recomputes width/height
// from content, these are only the pre-layout box.
const GROUP_DEFAULT_WIDTH = 900
const GROUP_DEFAULT_HEIGHT = 650

function a2aExtraHandlesForLabel(label: string): ExtraHandle[] | undefined {
  if (isRecruiterLabel(label)) {
    return [{ id: "target-right", type: "target", position: "right" }]
  }
  if (isDirectoryLabel(label)) {
    return [{ id: "source-left", type: "source", position: "left" }]
  }
  return undefined
}

export interface TopologyToFlowOptions {
  /** When false, skip SecurityClass check for tests. */
  validateUrls?: boolean
  /** When set, applies stable-agent UI map streaming vs publish GitHub display where applicable. */
  identityUiVariant?: IdentityUiGithubVariant
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

  // A single group node turns the workflow into a contained graph: members
  // become children (parentId/extent) and the transport renders compact.
  const groupRfIds = dedupedNodesIn
    .filter((n) => n.type === NODE_TYPES.GROUP)
    .map(rfIdOf)
  const groupRfId = groupRfIds.length === 1 ? groupRfIds[0] : null

  const labelByRfId = new Map<string, string>()
  for (const n of dedupedNodesIn) {
    labelByRfId.set(rfIdOf(n), typeof n.label === "string" ? n.label : "")
  }

  const nodes: Node[] = dedupedNodesIn.map((n): Node => {
    const rfId = rfIdOf(n)
    const position = positions.get(rfId) ?? { x: 0, y: 0 }
    const labelStr = labelByRfId.get(rfId) ?? ""
    const gh = resolveGithubFromAgentRecordUri(
      n.agent_record_uri as string | undefined,
      { validateUrls },
    )

    if (n.type === NODE_TYPES.GROUP) {
      return {
        id: rfId,
        type: NODE_TYPES.GROUP,
        position,
        data: { label: labelStr },
        style: {
          width: GROUP_DEFAULT_WIDTH,
          height: GROUP_DEFAULT_HEIGHT,
          backgroundColor: "var(--group-background)",
          border: "none",
          borderRadius: "8px",
        },
      }
    }

    const childProps = groupRfId
      ? { parentId: groupRfId, extent: "parent" as const }
      : {}

    if (n.type === NODE_TYPES.TRANSPORT) {
      const data: TransportNodeData = {
        label: labelStr || "Transport",
        githubLink: gh,
        compact: groupRfId != null,
      }
      return {
        id: rfId,
        type: NODE_TYPES.TRANSPORT,
        position,
        data: data as unknown as Record<string, unknown>,
        ...childProps,
      }
    }

    const { label1, label2 } = splitTopologyNodeLabel(labelStr)
    let data: CustomNodeData = {
      icon: resolveTopologyNodeIcon({ label1, label2 }),
      label1,
      label2,
      handles: HANDLE_TYPES.ALL,
      verificationStatus: VERIFICATION_STATUS.VERIFIED,
      githubLink: gh,
    }
    data = mergeAgenticTopologyIdentityUi(data, n, {
      validateUrls,
      identityUiVariant: options.identityUiVariant,
    })
    data = enrichAgenticTopologyWellKnownUi(data, n, { validateUrls })
    if (data.directoryAgentSlug) {
      data = {
        ...data,
        icon: resolveTopologyNodeIcon({
          label1: data.label1,
          label2: data.label2,
          directoryAgentSlug: data.directoryAgentSlug,
        }),
      }
    }
    const extraHandles = a2aExtraHandlesForLabel(labelStr)
    if (extraHandles) {
      data = { ...data, extraHandles }
    }

    return {
      id: rfId,
      type: NODE_TYPES.CUSTOM,
      position,
      data: data as unknown as Record<string, unknown>,
      ...childProps,
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
    const sourceLabel = labelByRfId.get(source) ?? ""
    const targetLabel = labelByRfId.get(target) ?? ""

    let label: string = EDGE_LABELS.A2A
    let sourceHandle: string | undefined
    let targetHandle: string | undefined
    if (isMcpServerLabel(targetLabel)) {
      label = EDGE_LABELS.MCP
    } else if (isDirectoryLabel(sourceLabel) && isRecruiterLabel(targetLabel)) {
      label = EDGE_LABELS.MCP_WITH_STDIO
      sourceHandle = "source-left"
      targetHandle = "target-right"
    }

    const base: Edge = {
      id: e.id,
      source,
      target,
      type: edgeType,
      data: { label },
    }
    if (sourceHandle) base.sourceHandle = sourceHandle
    if (targetHandle) base.targetHandle = targetHandle
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
