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
import {
  enrichAgenticTopologyWellKnownUi,
  mergeAgenticTopologyIdentityUi,
  resolveGithubFromAgentRecordUri,
  splitTopologyNodeLabel,
} from "@/utils/agenticTopologyIdentityUiMap"
import type { IdentityUiGithubVariant } from "@/utils/agenticTopologyIdentityUiMap"

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
        id: n.id,
        type: NODE_TYPES.TRANSPORT,
        position,
        data: data as unknown as Record<string, unknown>,
      }
    }

    const labelStr = typeof n.label === "string" ? n.label : ""
    const { label1, label2 } = splitTopologyNodeLabel(labelStr)
    let data: CustomNodeData = {
      icon: defaultCustomIcon(labelStr),
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
