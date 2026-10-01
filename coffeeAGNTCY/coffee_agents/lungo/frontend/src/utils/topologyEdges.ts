/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Edge half of `topologyWireToReactFlow`: wire edges to React Flow edges,
 * including duplicate collapsing, MCP/directory labels, and handle overrides.
 */

import type { Edge } from "@xyflow/react"
import type { TopologyEdgeWire } from "@/api/agenticWorkflowsTypes"
import {
  EDGE_LABELS,
  EDGE_TYPES,
  isDirectoryType,
  isMcpType,
} from "@/utils/const"
import {
  isDirectoryLabel,
  isMcpServerLabel,
  isRecruiterLabel,
} from "@/utils/agenticTopologyIdentityUiMap"

export interface TopologyEdgeContext {
  /** Wire id or trace-minted alias to canonical wire id. */
  canonical: (id: string | undefined) => string
  /** Canonical wire id to React Flow node id. */
  rfIdFor: (wireId: string | undefined) => string
  labelByRfId: Map<string, string>
  nodeTypeByRfId: Map<string, string | undefined>
  /** Appended to MCP edge labels when the topology declares a transport. */
  messageTransport: string | undefined
}

export function topologyWireEdgesToReactFlow(
  edgesIn: TopologyEdgeWire[],
  ctx: TopologyEdgeContext,
): Edge[] {
  const { canonical, rfIdFor, labelByRfId, nodeTypeByRfId, messageTransport } =
    ctx
  const seenEdgePairs = new Set<string>()
  const edges: Edge[] = []

  for (const e of edgesIn) {
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

  return edges
}
