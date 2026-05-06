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
import { layoutPositionsByLayer } from "@/utils/topologyLayout"
import { SecurityClass } from "@/utils/SecurityClass"

function splitLabel(label: string): { label1: string; label2: string } {
  const t = label.trim()
  if (!t) return { label1: "", label2: "" }
  const sp = t.indexOf(" ")
  if (sp === -1) return { label1: t, label2: "" }
  return { label1: t.slice(0, sp), label2: t.slice(sp + 1).trim() }
}

function defaultCustomIcon(label: string): React.ReactNode {
  const lower = label.toLowerCase()
  const iconSx = { fontSize: 16 } as const
  if (lower.includes("transport")) {
    return (
      <LocalShipping
        className="dark-icon opacity-100"
        sx={iconSx}
        aria-hidden
      />
    )
  }
  return <SmartToy className="dark-icon opacity-100" sx={iconSx} aria-hidden />
}

function inferGithubLink(agentRecordUri?: string): string | undefined {
  if (!agentRecordUri || typeof agentRecordUri !== "string") return undefined
  if (SecurityClass.isSafeExternalUrl(agentRecordUri)) return agentRecordUri
  return undefined
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

  const layerById = new Map<string, number>()
  for (const n of nodesIn) {
    if (n?.id) layerById.set(n.id, n.layer_index ?? 0)
  }
  const pos = layoutPositionsByLayer(
    nodesIn.map((n) => n.id).filter(Boolean),
    layerById,
  )

  const nodes: Node[] = nodesIn.map((raw): Node => {
    const n = raw as TopologyNodeWire
    const nodeType =
      n.type === NODE_TYPES.TRANSPORT ? NODE_TYPES.TRANSPORT : NODE_TYPES.CUSTOM
    const position = pos.get(n.id) ?? { x: 0, y: 0 }
    const gh = inferGithubLink(n.agent_record_uri as string | undefined)
    const safeGh =
      gh && (!validateUrls || SecurityClass.isSafeExternalUrl(gh))
        ? gh
        : undefined

    if (nodeType === NODE_TYPES.TRANSPORT) {
      const data: TransportNodeData = {
        label: typeof n.label === "string" ? n.label : "Transport",
        githubLink: safeGh,
        compact: false,
      }
      return {
        id: n.id,
        type: NODE_TYPES.TRANSPORT,
        position,
        data: data as unknown as Record<string, unknown>,
      }
    }

    const labelStr = typeof n.label === "string" ? n.label : ""
    const { label1, label2 } = splitLabel(labelStr)
    const data: CustomNodeData = {
      icon: defaultCustomIcon(labelStr),
      label1,
      label2,
      handles: HANDLE_TYPES.ALL,
      verificationStatus: VERIFICATION_STATUS.VERIFIED,
      githubLink: safeGh,
      slug:
        typeof n.stable_agent_id === "string"
          ? n.stable_agent_id.replace(/^agent:\/\//, "")
          : undefined,
    }

    return {
      id: n.id,
      type: NODE_TYPES.CUSTOM,
      position,
      data: data as unknown as Record<string, unknown>,
    }
  })

  const edges: Edge[] = edgesIn.map((raw): Edge => {
    const e = raw as TopologyEdgeWire
    const edgeType =
      e.type === EDGE_TYPES.BRANCHING ? EDGE_TYPES.BRANCHING : EDGE_TYPES.CUSTOM
    const base: Edge = {
      id: e.id,
      source: e.source ?? "",
      target: e.target ?? "",
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
    return base
  })

  return { nodes, edges }
}
