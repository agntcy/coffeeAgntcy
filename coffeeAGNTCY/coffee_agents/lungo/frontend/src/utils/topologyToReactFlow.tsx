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
  DISPLAY_NODE_TYPES,
  EDGE_LABELS,
  EDGE_TYPES,
  HANDLE_TYPES,
  VERIFICATION_STATUS,
  canonicalizeNodeType,
  isDirectoryType,
  isGroupType,
  isMcpType,
  isTransportType,
  nodeTypeToDisplayType,
} from "@/utils/const"
import { flowNodeDataRecord } from "@/components/MainArea/Graph/Elements/nodes/customNodeData"
import type {
  CustomNodeData,
  ExtraHandle,
  TransportNodeData,
} from "@/components/MainArea/Graph/Elements/nodes/types"
import {
  layoutPositionsByLayer,
  layoutSlimTransportGraph,
} from "@/utils/topologyLayout"
import {
  applyBackendTopologyWireFields,
  applyDiscoveredAgentInlineUi,
  directoryAgentSlugFromAgentRecordUri,
  enrichAgenticTopologyWellKnownUi,
  isDirectoryLabel,
  isMcpServerLabel,
  isRecruiterLabel,
  resolveGithubFromAgentRecordUri,
  splitTopologyNodeLabel,
} from "@/utils/agenticTopologyIdentityUiMap"
import { resolveTopologyNodeIcon } from "@/utils/topologyNodeIcons"
import { transportGithubLink } from "@/utils/transportGithub"

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

function stripTransportLabelPrefix(label: string): string {
  const trimmed = label.trim()
  const lower = trimmed.toLowerCase()
  const prefix = "transport:"
  if (lower.startsWith(prefix)) {
    return trimmed.slice(prefix.length).trim()
  }
  return trimmed
}

function normalizedTransportKey(label: string | undefined): string {
  const stripped =
    typeof label === "string" ? stripTransportLabelPrefix(label) : ""
  const lower = stripped.toLowerCase()
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

function canonicalTypeOf(n: TopologyNodeWire): string | undefined {
  return canonicalizeNodeType(typeof n.type === "string" ? n.type : undefined)
}

function dedupKeyFor(
  n: TopologyNodeWire,
  nodeType: string | undefined,
): string {
  const sid = extractStableAgentId(n)
  if (sid) return `sid::${sid}`
  const typeKey = nodeTypeToDisplayType(nodeType)
  const labelKey =
    typeKey === DISPLAY_NODE_TYPES.TRANSPORT
      ? normalizedTransportKey(n.label)
      : typeof n.label === "string"
        ? n.label.trim().toLowerCase()
        : ""
  return `lbl::${typeKey}::${labelKey}`
}

function rfIdForNode(
  n: TopologyNodeWire,
  nodeType: string | undefined,
): string {
  const sid = extractStableAgentId(n)
  if (sid) return sid
  if (isTransportType(nodeType)) {
    return transportCanonicalRfId(n.label)
  }
  return n.id
}

function a2aExtraHandlesForNode(
  label: string,
  nodeType: string | undefined,
): ExtraHandle[] | undefined {
  if (isRecruiterLabel(label)) {
    return [{ id: "target-right", type: "target", position: "right" }]
  }
  if (isDirectoryType(nodeType) || isDirectoryLabel(label)) {
    return [{ id: "source-left", type: "source", position: "left" }]
  }
  return undefined
}

export interface TopologyToFlowOptions {
  /** When false, skip SecurityClass check for tests. */
  validateUrls?: boolean
  /** When true, transport GitHub links use the streaming variant paths. */
  isStreaming?: boolean
}

function messageTransportFromNodes(
  nodes: TopologyNodeWire[],
  nodeTypeByWireId: Map<string, string | undefined>,
): string | undefined {
  for (const n of nodes) {
    if (!isTransportType(nodeTypeByWireId.get(n.id))) continue
    const value = n.message_transport
    if (typeof value === "string" && value.trim()) return value.trim()
  }
  return undefined
}

export function topologyWireToReactFlow(
  topology: TopologyWire | undefined | null,
  options: TopologyToFlowOptions = {},
): { nodes: Node[]; edges: Edge[] } {
  const validateUrls = options.validateUrls !== false
  const isStreaming = options.isStreaming === true
  const nodesIn = topology?.nodes ?? []
  const edgesIn = topology?.edges ?? []

  // Collapse trace-minted node://UUID aliases via stable_agent_id; fall back
  // to a (type, label) tuple for seed nodes that lack the field.
  const aliasToCanonical = new Map<string, string>()
  const canonicalKeyToId = new Map<string, string>()
  const canonicalIdToNode = new Map<string, TopologyNodeWire>()
  const dedupedNodesIn: TopologyNodeWire[] = []
  for (const n of nodesIn) {
    if (!n?.id) continue
    const incomingType = canonicalTypeOf(n)
    const dedupKey = dedupKeyFor(n, incomingType)
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
          isTransportType(canonicalTypeOf(prev)) &&
          CONCRETE_TRANSPORTS.has(prevLabel.trim().toLowerCase())
        const nextIsConcreteTransport =
          isTransportType(incomingType) &&
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

  const nodeTypeByWireId = new Map<string, string | undefined>()
  const rfIdByWireId = new Map<string, string>()
  const layoutRfIds: string[] = []
  for (const n of dedupedNodesIn) {
    const nodeType = canonicalTypeOf(n)
    const rfId = rfIdForNode(n, nodeType)
    nodeTypeByWireId.set(n.id, nodeType)
    rfIdByWireId.set(n.id, rfId)
    layoutRfIds.push(rfId)
  }

  const wireIdToRfId = new Map<string, string>(rfIdByWireId)
  for (const [alias, can] of aliasToCanonical.entries()) {
    const rf = wireIdToRfId.get(can)
    if (rf) wireIdToRfId.set(alias, rf)
  }
  const rfIdFor = (wireId: string | undefined): string =>
    wireId ? (wireIdToRfId.get(wireId) ?? wireId) : ""

  const layerById = new Map<string, number>()
  const positions = new Map<string, { x: number; y: number }>()
  const labelByRfId = new Map<string, string>()
  const nodeTypeByRfId = new Map<string, string | undefined>()
  const groupRfIds: string[] = []
  for (const n of dedupedNodesIn) {
    const rfId = rfIdByWireId.get(n.id)
    const nodeType = nodeTypeByWireId.get(n.id)
    if (!rfId) continue
    layerById.set(rfId, n.layer_index ?? 0)
    labelByRfId.set(rfId, typeof n.label === "string" ? n.label : "")
    nodeTypeByRfId.set(rfId, nodeType)
    if (isGroupType(nodeType)) {
      groupRfIds.push(rfId)
    }
  }
  const pos = layoutPositionsByLayer(layoutRfIds, layerById)
  for (const n of dedupedNodesIn) {
    const rfId = rfIdByWireId.get(n.id)
    if (!rfId) continue
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
  const groupRfId = groupRfIds.length === 1 ? groupRfIds[0] : null
  const messageTransport = messageTransportFromNodes(
    dedupedNodesIn,
    nodeTypeByWireId,
  )

  const nodes: Node[] = dedupedNodesIn.map((n): Node => {
    const rfId = rfIdByWireId.get(n.id) ?? n.id
    const position = positions.get(rfId) ?? { x: 0, y: 0 }
    const labelStr = labelByRfId.get(rfId) ?? ""
    const nodeType = nodeTypeByWireId.get(n.id)
    const displayType = nodeTypeToDisplayType(nodeType)
    const gh = resolveGithubFromAgentRecordUri(
      n.agent_record_uri as string | undefined,
      { validateUrls },
    )

    if (isGroupType(nodeType)) {
      // The group is never drawn; it only exists so children can anchor to it
      // via parentId/extent. width/height must live on the node (not style) so
      // extent clamping still resolves the box while the node stays hidden.
      return {
        id: rfId,
        type: displayType,
        position,
        hidden: true,
        width: GROUP_DEFAULT_WIDTH,
        height: GROUP_DEFAULT_HEIGHT,
        data: { nodeType },
      }
    }

    const childProps = groupRfId
      ? { parentId: groupRfId, extent: "parent" as const }
      : {}

    if (isTransportType(nodeType)) {
      const transportName =
        typeof n.message_transport === "string"
          ? n.message_transport
          : undefined
      const transportGithub =
        transportName != null
          ? transportGithubLink(transportName, isStreaming)
          : gh
      const data: TransportNodeData = {
        nodeType,
        label: labelStr || "Transport",
        githubLink: transportGithub,
        compact: groupRfId != null,
      }
      return {
        id: rfId,
        type: displayType,
        position,
        data: flowNodeDataRecord(data),
        ...childProps,
      }
    }

    // Curated subtitle from the wire (event_v1 >= 1.1.0) wins; otherwise
    // fall back to splitting the single label (older minors / discovered nodes).
    const wireLabelSubtitle =
      typeof n.label_subtitle === "string" ? n.label_subtitle.trim() : ""
    const split = splitTopologyNodeLabel(labelStr)
    const label = wireLabelSubtitle ? labelStr : split.label
    const label_subtitle = wireLabelSubtitle
      ? wireLabelSubtitle
      : split.label_subtitle
    const directoryAgentSlug = directoryAgentSlugFromAgentRecordUri(
      n.agent_record_uri as string | undefined,
    )
    let data: CustomNodeData = {
      nodeType,
      icon: resolveTopologyNodeIcon({
        label,
        label_subtitle,
        nodeType,
      }),
      label,
      label_subtitle,
      handles: HANDLE_TYPES.ALL,
      verificationStatus: VERIFICATION_STATUS.VERIFIED,
      githubLink: gh,
      ...(directoryAgentSlug ? { directoryAgentSlug } : {}),
    }
    data = applyBackendTopologyWireFields(data, n, { validateUrls })
    data = enrichAgenticTopologyWellKnownUi(data, n, { validateUrls })
    data = applyDiscoveredAgentInlineUi(data, n)
    if (data.directoryAgentSlug) {
      data = {
        ...data,
        icon: resolveTopologyNodeIcon({
          label: data.label,
          label_subtitle: data.label_subtitle,
          directoryAgentSlug: data.directoryAgentSlug,
          nodeType: data.nodeType,
        }),
      }
    }
    const extraHandles = a2aExtraHandlesForNode(labelStr, nodeType)
    if (extraHandles) {
      data = { ...data, extraHandles }
    }

    return {
      id: rfId,
      type: displayType,
      position,
      data: flowNodeDataRecord(data),
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
    const targetType = nodeTypeByRfId.get(target)
    const sourceType = nodeTypeByRfId.get(source)
    if (isMcpType(targetType) || isMcpServerLabel(targetLabel)) {
      label = messageTransport
        ? `${EDGE_LABELS.MCP}${messageTransport}`
        : EDGE_LABELS.MCP
    } else if (
      (isDirectoryType(sourceType) || isDirectoryLabel(sourceLabel)) &&
      isRecruiterLabel(targetLabel)
    ) {
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
