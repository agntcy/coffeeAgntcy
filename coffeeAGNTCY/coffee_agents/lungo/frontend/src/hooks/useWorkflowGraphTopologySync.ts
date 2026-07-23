/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useCallback, useRef } from "react"
import type { Edge, Node } from "@xyflow/react"
import {
  getWorkflowInstanceState,
  instanceIdToPathUuid,
} from "@/api/agenticWorkflowsClient"
import type { TopologyWire } from "@/api/agenticWorkflowsTypes"
import { logger } from "@/utils/logger"
import { topologyWireToReactFlow } from "@/utils/topologyToReactFlow"
import {
  REFETCH_DEBOUNCE_MS,
  type WorkflowGraphAgenticSession,
} from "./useWorkflowGraphFromAgenticApi.types"

interface UseWorkflowGraphTopologySyncParams {
  isStreamingRef: React.RefObject<boolean>
  sessionRef: React.RefObject<WorkflowGraphAgenticSession | null>
  onAppliedRef: React.RefObject<
    ((nodeIds: readonly string[]) => void) | undefined
  >
  attachHandlers: (node: Node) => Node
  setNodes: React.Dispatch<React.SetStateAction<Node[]>>
  setEdges: React.Dispatch<React.SetStateAction<Edge[]>>
  restoreEdgeAnimation: () => void
}

export function useWorkflowGraphTopologySync({
  isStreamingRef,
  sessionRef,
  onAppliedRef,
  attachHandlers,
  setNodes,
  setEdges,
  restoreEdgeAnimation,
}: UseWorkflowGraphTopologySyncParams) {
  const lastAppliedGraphNodeIdsRef = useRef<Set<string>>(new Set())

  const applyInstanceTopology = useCallback(
    (topology: TopologyWire | undefined) => {
      const { nodes: mappedNodes, edges: mappedEdges } =
        topologyWireToReactFlow(topology, {
          isStreaming: isStreamingRef.current,
        })
      const withHandlers = mappedNodes.map(attachHandlers)
      lastAppliedGraphNodeIdsRef.current = new Set(
        withHandlers.map((n) => n.id),
      )
      setNodes(withHandlers)
      setEdges(mappedEdges)
      onAppliedRef.current?.(withHandlers.map((node) => node.id))
      queueMicrotask(() => {
        restoreEdgeAnimation()
      })
    },
    [
      attachHandlers,
      isStreamingRef,
      onAppliedRef,
      restoreEdgeAnimation,
      setEdges,
      setNodes,
    ],
  )

  const applyInstanceTopologyRef = useRef(applyInstanceTopology)
  applyInstanceTopologyRef.current = applyInstanceTopology

  const refetchAndApplyTopology = useCallback(
    async (seq: number, attempt: number) => {
      const latest = sessionRef.current
      if (!latest || latest.refetchSeq !== seq) return
      try {
        const path = instanceIdToPathUuid(latest.instanceId)
        const fresh = await getWorkflowInstanceState(
          latest.client,
          latest.workflowName,
          path,
          true,
        )
        const stillLatest = sessionRef.current
        if (!stillLatest || stillLatest.refetchSeq !== seq) return
        applyInstanceTopologyRef.current(fresh.topology)
      } catch (e) {
        logger.apiError("agentic-workflows/refetch-topology", e)
        const s = sessionRef.current
        if (!s || s.refetchSeq !== seq) return
        if (attempt >= 2) return
        const backoffMs = attempt === 0 ? 200 : 500
        if (s.retryTimer) clearTimeout(s.retryTimer)
        s.retryTimer = setTimeout(() => {
          const current = sessionRef.current
          if (current) current.retryTimer = null
          if (!current || current.refetchSeq !== seq) return
          void refetchAndApplyTopologyRef.current(seq, attempt + 1)
        }, backoffMs)
      }
    },
    [sessionRef],
  )

  const refetchAndApplyTopologyRef = useRef(refetchAndApplyTopology)
  refetchAndApplyTopologyRef.current = refetchAndApplyTopology

  const scheduleTopologyRefetch = useCallback(() => {
    const s = sessionRef.current
    if (!s) return
    s.refetchSeq += 1
    const seq = s.refetchSeq
    if (s.debounceTimer) clearTimeout(s.debounceTimer)
    if (s.retryTimer) {
      clearTimeout(s.retryTimer)
      s.retryTimer = null
    }
    s.debounceTimer = setTimeout(() => {
      const latest = sessionRef.current
      if (!latest || latest.refetchSeq !== seq) return
      latest.debounceTimer = null
      void refetchAndApplyTopologyRef.current(seq, 0)
    }, REFETCH_DEBOUNCE_MS)
  }, [sessionRef])

  const scheduleTopologyRefetchRef = useRef(scheduleTopologyRefetch)
  scheduleTopologyRefetchRef.current = scheduleTopologyRefetch

  return {
    applyInstanceTopologyRef,
    scheduleTopologyRefetchRef,
    lastAppliedGraphNodeIdsRef,
  }
}
