/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { Edge, Node } from "@xyflow/react"
import type { createClient } from "@/api/agenticWorkflowsClient"
import type { CustomNodeData } from "@/components/MainArea/Graph/Elements/types"
import type { PatternType } from "@/utils/patternUtils"
import type { WorkflowSummary } from "@/utils/agenticWorkflowsApi"

export const REFETCH_DEBOUNCE_MS = 80
/** Auto-clear messaging highlights if no newer event refreshes them. */
export const MESSAGING_HIGHLIGHT_TTL_MS = 2_500

export function mergeDiscoveryNodes(base: Node[], prev: Node[]): Node[] {
  const overlay = prev.filter((n) => n.id.startsWith("discovery-"))
  if (overlay.length === 0) return base
  return [...base, ...overlay]
}

export function mergeDiscoveryEdges(base: Edge[], prev: Edge[]): Edge[] {
  const overlay = prev.filter(
    (e) =>
      e.source.startsWith("discovery-") || e.target.startsWith("discovery-"),
  )
  if (overlay.length === 0) return base
  const ids = new Set(base.map((e) => e.id))
  return [...base, ...overlay.filter((e) => !ids.has(e.id))]
}

export interface UseWorkflowGraphFromAgenticApiParams {
  pattern: PatternType
  selectedWorkflowSummary: WorkflowSummary | null
  setNodes: React.Dispatch<React.SetStateAction<Node[]>>
  setEdges: React.Dispatch<React.SetStateAction<Edge[]>>
  handleOpenIdentityModal: (nodeId: string, nodeData: CustomNodeData) => void
  handleOpenOasfModal: (nodeData: CustomNodeData) => void
  onTopologyApplied?: () => void
}

export interface UseWorkflowGraphFromAgenticApiResult {
  /** True when the pattern maps to a catalog workflow (uses same API base as LHS menu). */
  agenticMode: boolean
  agenticError: string | null
  /** Active workflow instance id (e.g. ``instance://<uuid>``) once instantiated. */
  workflowInstanceId: string | null
  /**
   * True when this pattern has a static graph in `graphConfigsData` and the
   * hook is deferring all positioning to it. Callers should still run their
   * normal static-graph reconciliation (config sync on pattern change) even
   * though `agenticMode` is true.
   */
  staticIdMapActive: boolean
  /** Restore edge animation after a static-config rebuild wipes it. */
  restoreEdgeAnimation: () => void
}

export type WorkflowGraphAgenticSession = {
  client: ReturnType<typeof createClient>
  baseUrl: string
  workflowName: string
  instanceId: string
  pathUuid: string
  closeSse: (() => void) | null
  debounceTimer: ReturnType<typeof setTimeout> | null
  retryTimer: ReturnType<typeof setTimeout> | null
  refetchSeq: number
  sseReconnectAttempts: number
}
