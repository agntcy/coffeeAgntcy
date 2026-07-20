/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { Edge, Node } from "@xyflow/react"
import type { CustomNodeData } from "@/components/MainArea/Graph/Elements/types"
import type { PatternType } from "@/utils/patternUtils"
import type { WorkflowSummary } from "@/utils/agenticWorkflowsApi"

export const REFETCH_DEBOUNCE_MS = 80
/** Linear SSE reconnect delay: attempt N waits N × this value (ms). */
export const SSE_RECONNECT_BACKOFF_MS = 250
/** Auto-clear messaging highlights if no newer event refreshes them. */
export const MESSAGING_HIGHLIGHT_TTL_MS = 2_500

export interface UseWorkflowGraphFromAgenticApiParams {
  pattern: PatternType
  selectedWorkflowSummary: WorkflowSummary | null
  setNodes: React.Dispatch<React.SetStateAction<Node[]>>
  setEdges: React.Dispatch<React.SetStateAction<Edge[]>>
  handleOpenIdentityModal: (nodeId: string, nodeData: CustomNodeData) => void
  handleOpenOasfModal: (nodeData: CustomNodeData) => void
  onTopologyApplied?: (nodeIds: readonly string[]) => void
}

export interface UseWorkflowGraphFromAgenticApiResult {
  /** True when the pattern maps to a catalog workflow (uses same API base as LHS menu). */
  agenticMode: boolean
  agenticError: string | null
  /** Active workflow instance id (e.g. ``instance://<uuid>``) once instantiated. */
  workflowInstanceId: string | null
}

export type WorkflowGraphAgenticSession = {
  baseUrl: string
  workflowName: string
  instanceId: string
  pathUuid: string
  closeSse: (() => void) | null
  debounceTimer: ReturnType<typeof setTimeout> | null
  retryTimer: ReturnType<typeof setTimeout> | null
  sseReconnectTimer: ReturnType<typeof setTimeout> | null
  refetchSeq: number
  sseReconnectAttempts: number
}
