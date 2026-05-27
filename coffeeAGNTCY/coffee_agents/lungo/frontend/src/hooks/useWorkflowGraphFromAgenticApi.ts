/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import type { Edge, Node } from "@xyflow/react"
import {
  deleteWorkflowInstance,
  instanceIdToPathUuid,
} from "@/api/agenticWorkflowsClient"
import type { EventV1Wire } from "@/api/agenticWorkflowsTypes"
import type { CustomNodeData } from "@/components/MainArea/Graph/Elements/types"
import {
  getAgenticWorkflowsApiUrl,
  mapWorkflowNameToSlug,
  type WorkflowSummary,
} from "@/utils/agenticWorkflowsApi"
import { logger } from "@/utils/logger"
import type { PatternType } from "@/utils/patternUtils"
import { useActiveWorkflowInstanceStore } from "@/stores/activeWorkflowInstanceStore"
import { identityUiVariantForPattern } from "@/utils/agenticTopologyIdentityUiMap"
import { topologyWireToReactFlow } from "@/utils/topologyToReactFlow"
import {
  staticIdMapForPattern,
  type StaticIdMap,
} from "@/utils/topologyStaticIdMap"
import {
  patchGraphActiveHighlight,
  type MessagingHighlightIds,
} from "@/utils/workflowEventMessagingHighlight"
import {
  bootstrapAgenticWorkflowGraph,
  handleAgenticWorkflowInstanceSseEvent,
  mergeDiscoveryEdges,
  mergeDiscoveryNodes,
  refetchAndApplyAgenticTopology,
  scheduleAgenticTopologyRefetch,
  type AgenticWorkflowSession,
  type WorkflowGraphAgenticSessionRefs,
} from "@/utils/workflowGraphAgenticInstanceSession"

/** Auto-clear messaging highlights if no newer event refreshes them. */
const MESSAGING_HIGHLIGHT_TTL_MS = 2_500

export interface UseWorkflowGraphFromAgenticApiParams {
  pattern: PatternType
  selectedWorkflowSummary: WorkflowSummary | null
  setNodes: React.Dispatch<React.SetStateAction<Node[]>>
  setEdges: React.Dispatch<React.SetStateAction<Edge[]>>
  handleOpenIdentityModal: (
    nodeData: CustomNodeData,
    position: { x: number; y: number },
    nodeName?: string,
    data?: CustomNodeData,
    isMcpServer?: boolean,
  ) => void
  handleOpenOasfModal: (
    nodeData: CustomNodeData,
    position: { x: number; y: number },
  ) => void
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

export function useWorkflowGraphFromAgenticApi({
  pattern,
  selectedWorkflowSummary,
  setNodes,
  setEdges,
  handleOpenIdentityModal,
  handleOpenOasfModal,
  onTopologyApplied,
}: UseWorkflowGraphFromAgenticApiParams): UseWorkflowGraphFromAgenticApiResult {
  const baseUrl = useMemo(
    () => getAgenticWorkflowsApiUrl().replace(/\/$/, ""),

    [],
  )
  const workflowName = selectedWorkflowSummary?.name ?? null
  const agenticMode = Boolean(
    selectedWorkflowSummary &&
    workflowName &&
    mapWorkflowNameToSlug(workflowName) === pattern,
  )

  /**
   * When a pattern ships with a static graph in `graphConfigsData.tsx`
   * (P/S, GroupComm, Discovery), an id map routes dynamic event ids onto
   * the static NODE_IDS. In that mode we keep the static graph's
   * hand-tuned positions, icons, and data intact; only the live-event
   * highlight/animation pipeline runs.
   */
  const staticIdMap: StaticIdMap | null = useMemo(
    () => staticIdMapForPattern(pattern),
    [pattern],
  )
  const staticIdMapRef = useRef(staticIdMap)
  staticIdMapRef.current = staticIdMap

  const [agenticError, setAgenticError] = useState<string | null>(null)
  const workflowInstanceId = useActiveWorkflowInstanceStore(
    (s) => s.workflowInstanceId,
  )
  const setWorkflowInstanceId = useActiveWorkflowInstanceStore(
    (s) => s.setWorkflowInstanceId,
  )
  const sessionRef = useRef<AgenticWorkflowSession | null>(null)
  /** Latest graph node ids after topology merge (for highlight id overlap checks). */
  const lastAppliedGraphNodeIdsRef = useRef<Set<string>>(new Set())
  const lastMessagingHighlightRef = useRef<MessagingHighlightIds>({
    nodeIds: new Set(),
    edgeIds: new Set(),
    edgePairs: new Set(),
  })
  const highlightTtlTimerRef = useRef<ReturnType<typeof setTimeout> | null>(
    null,
  )

  const patternRef = useRef(pattern)
  patternRef.current = pattern

  const identityRef = useRef(handleOpenIdentityModal)
  const oasfRef = useRef(handleOpenOasfModal)
  const onAppliedRef = useRef(onTopologyApplied)
  identityRef.current = handleOpenIdentityModal
  oasfRef.current = handleOpenOasfModal
  onAppliedRef.current = onTopologyApplied

  const agenticSessionRefs = useRef<WorkflowGraphAgenticSessionRefs>({
    sessionRef,
    staticIdMapRef,
    lastMessagingHighlightRef,
    applyInstanceTopologyRef: { current: () => {} },
    refetchAndApplyTopologyRef: { current: async () => {} },
    scheduleTopologyRefetchRef: { current: () => {} },
  })

  const attachHandlers = useCallback((node: Node): Node => {
    return {
      ...node,
      data: {
        ...node.data,
        onOpenIdentityModal: identityRef.current,
        onOpenOasfModal: oasfRef.current,
        isModalOpen: false,
      },
    }
  }, [])

  const restoreEdgeAnimation = useCallback(() => {
    const h = lastMessagingHighlightRef.current
    setNodes((prev) => patchGraphActiveHighlight(prev, [], h).nodes)
    setEdges((prev) => {
      const { edges } = patchGraphActiveHighlight([], prev, h)
      return edges
    })
  }, [setNodes, setEdges])

  const clearMessagingHighlightTtl = useCallback(() => {
    if (highlightTtlTimerRef.current !== null) {
      clearTimeout(highlightTtlTimerRef.current)
      highlightTtlTimerRef.current = null
    }
  }, [])

  const clearMessagingHighlightVisual = useCallback(() => {
    lastMessagingHighlightRef.current = {
      nodeIds: new Set(),
      edgeIds: new Set(),
      edgePairs: new Set(),
    }
    const h = lastMessagingHighlightRef.current
    setNodes((prev) => patchGraphActiveHighlight(prev, [], h).nodes)
    setEdges((prev) => patchGraphActiveHighlight([], prev, h).edges)
  }, [setNodes, setEdges])

  const scheduleMessagingHighlightTtl = useCallback(() => {
    clearMessagingHighlightTtl()
    highlightTtlTimerRef.current = setTimeout(() => {
      highlightTtlTimerRef.current = null
      clearMessagingHighlightVisual()
    }, MESSAGING_HIGHLIGHT_TTL_MS)
  }, [clearMessagingHighlightTtl, clearMessagingHighlightVisual])

  const applyInstanceTopology = useCallback(
    (
      topology: import("@/api/agenticWorkflowsTypes").TopologyWire | undefined,
    ) => {
      // When a static id map governs the current pattern, we leave the
      // graphConfigsData-sourced nodes/edges alone — positions, icons, and
      // node data are authored statically. The SSE pipeline still runs and
      // patches highlights/animation on top.
      if (staticIdMapRef.current) {
        onAppliedRef.current?.()
        queueMicrotask(() => {
          restoreEdgeAnimation()
        })
        return
      }
      const { nodes: mappedNodes, edges: mappedEdges } =
        topologyWireToReactFlow(topology, {
          identityUiVariant: identityUiVariantForPattern(patternRef.current),
        })
      const withHandlers = mappedNodes.map(attachHandlers)
      setNodes((prev) => {
        const merged = mergeDiscoveryNodes(withHandlers, prev)
        lastAppliedGraphNodeIdsRef.current = new Set(merged.map((n) => n.id))
        return merged
      })
      setEdges((prev) => mergeDiscoveryEdges(mappedEdges, prev))
      onAppliedRef.current?.()
      queueMicrotask(() => {
        restoreEdgeAnimation()
      })
    },
    [attachHandlers, setNodes, setEdges, restoreEdgeAnimation],
  )

  const applyInstanceTopologyRef = useRef(applyInstanceTopology)
  applyInstanceTopologyRef.current = applyInstanceTopology
  agenticSessionRefs.current.applyInstanceTopologyRef = applyInstanceTopologyRef

  const clearSession = useCallback(() => {
    const s = sessionRef.current
    if (!s) return
    if (s.closeSse) s.closeSse()
    if (s.debounceTimer) clearTimeout(s.debounceTimer)
    if (s.retryTimer) clearTimeout(s.retryTimer)
    const { client, workflowName, instanceId } = s
    sessionRef.current = null
    try {
      const pathUuid = instanceIdToPathUuid(instanceId)
      void deleteWorkflowInstance(client, workflowName, pathUuid).catch(
        (err) => {
          logger.apiError("agentic-workflows/delete-instance", err)
        },
      )
    } catch {
      // instance id may be malformed during teardown
    }
    setWorkflowInstanceId(null)
    clearMessagingHighlightTtl()
    lastMessagingHighlightRef.current = {
      nodeIds: new Set(),
      edgeIds: new Set(),
      edgePairs: new Set(),
    }
  }, [clearMessagingHighlightTtl, setWorkflowInstanceId])

  const clearSessionRef = useRef(clearSession)
  clearSessionRef.current = clearSession

  const refetchAndApplyTopology = useCallback(
    async (seq: number, attempt: number) => {
      await refetchAndApplyAgenticTopology(
        agenticSessionRefs.current,
        seq,
        attempt,
      )
    },
    [],
  )

  const refetchAndApplyTopologyRef = useRef(refetchAndApplyTopology)
  refetchAndApplyTopologyRef.current = refetchAndApplyTopology
  agenticSessionRefs.current.refetchAndApplyTopologyRef =
    refetchAndApplyTopologyRef

  const scheduleTopologyRefetch = useCallback(() => {
    scheduleAgenticTopologyRefetch(agenticSessionRefs.current)
  }, [])

  const scheduleTopologyRefetchRef = useRef(scheduleTopologyRefetch)
  scheduleTopologyRefetchRef.current = scheduleTopologyRefetch
  agenticSessionRefs.current.scheduleTopologyRefetchRef =
    scheduleTopologyRefetchRef

  const handleWorkflowInstanceSseEvent = useCallback(
    (ev: EventV1Wire, catalogWorkflowName: string, instanceId: string) => {
      handleAgenticWorkflowInstanceSseEvent(
        agenticSessionRefs.current,
        setNodes,
        setEdges,
        scheduleMessagingHighlightTtl,
        ev,
        catalogWorkflowName,
        instanceId,
      )
    },
    [setNodes, setEdges, scheduleMessagingHighlightTtl],
  )

  const handleWorkflowInstanceSseEventRef = useRef(
    handleWorkflowInstanceSseEvent,
  )
  handleWorkflowInstanceSseEventRef.current = handleWorkflowInstanceSseEvent

  useEffect(() => {
    const catalogWorkflowName = selectedWorkflowSummary?.name
    if (!agenticMode || !baseUrl || !catalogWorkflowName) {
      clearSessionRef.current()
      setAgenticError(null)
      return
    }

    clearSessionRef.current()

    let cancelled = false

    const run = async () => {
      setAgenticError(null)
      await bootstrapAgenticWorkflowGraph({
        baseUrl,
        catalogWorkflowName,
        isCancelled: () => cancelled,
        sessionRef,
        applyInstanceTopology: (topology) => {
          applyInstanceTopologyRef.current(topology)
        },
        setWorkflowInstanceId,
        setAgenticError: (message) => setAgenticError(message),
        onSseEvent: (ev, name, instanceId) => {
          handleWorkflowInstanceSseEventRef.current(ev, name, instanceId)
        },
      })
    }

    void run()

    return () => {
      cancelled = true
      clearSessionRef.current()
    }
  }, [
    agenticMode,
    baseUrl,
    selectedWorkflowSummary?.name,
    setWorkflowInstanceId,
  ])

  return {
    agenticMode,
    agenticError,
    workflowInstanceId,
    staticIdMapActive: staticIdMap !== null,
    restoreEdgeAnimation,
  }
}
