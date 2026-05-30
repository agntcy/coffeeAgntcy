/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import type { Edge, Node } from "@xyflow/react"
import {
  createClient,
  eventTouchesInstance,
  getWorkflowInstanceState,
  instanceIdToPathUuid,
  instantiateWorkflow,
  subscribeWorkflowInstanceSse,
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
  extractInstanceTopologyFromEvent,
  messagingHighlightIdsFromTopology,
  patchGraphActiveHighlight,
  staticGraphHighlightIdsFromTopology,
  type MessagingHighlightIds,
} from "@/utils/workflowEventMessagingHighlight"

const REFETCH_DEBOUNCE_MS = 80
/** Auto-clear messaging highlights if no newer event refreshes them. */
const MESSAGING_HIGHLIGHT_TTL_MS = 2_500

function mergeDiscoveryNodes(base: Node[], prev: Node[]): Node[] {
  const overlay = prev.filter((n) => n.id.startsWith("discovery-"))
  if (overlay.length === 0) return base
  return [...base, ...overlay]
}

function mergeDiscoveryEdges(base: Edge[], prev: Edge[]): Edge[] {
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
  handleOpenIdentityModal: (nodeData: CustomNodeData) => void
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
  type Session = {
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
  const sessionRef = useRef<Session | null>(null)
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

  const clearSession = useCallback(() => {
    const s = sessionRef.current
    if (!s) return
    if (s.closeSse) s.closeSse()
    if (s.debounceTimer) clearTimeout(s.debounceTimer)
    if (s.retryTimer) clearTimeout(s.retryTimer)
    sessionRef.current = null
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
    [],
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
  }, [])

  const scheduleTopologyRefetchRef = useRef(scheduleTopologyRefetch)
  scheduleTopologyRefetchRef.current = scheduleTopologyRefetch

  const handleWorkflowInstanceSseEvent = useCallback(
    (ev: EventV1Wire, catalogWorkflowName: string, instanceId: string) => {
      if (!eventTouchesInstance(ev, catalogWorkflowName, instanceId)) return

      const partial = extractInstanceTopologyFromEvent(
        ev,
        catalogWorkflowName,
        instanceId,
      )
      // When a static id map is active, derive highlight ids in the static
      // namespace directly from the wire labels/stable_agent_ids — this is
      // what lets the live event animation light up the static nodes laid
      // out by graphConfigsData.tsx. Otherwise use the legacy path which
      // operates in the dynamic id namespace.
      const idMap = staticIdMapRef.current
      let ids: MessagingHighlightIds
      if (idMap) {
        ids = staticGraphHighlightIdsFromTopology(partial, idMap)
      } else {
        ids = messagingHighlightIdsFromTopology(partial)
      }
      const hasAny = ids.nodeIds.size > 0 || ids.edgeIds.size > 0
      if (hasAny) {
        lastMessagingHighlightRef.current = {
          nodeIds: new Set(ids.nodeIds),
          edgeIds: new Set(ids.edgeIds),
          edgePairs: new Set(ids.edgePairs),
        }
        setNodes(
          (prev) =>
            patchGraphActiveHighlight(
              prev,
              [],
              lastMessagingHighlightRef.current,
            ).nodes,
        )
        setEdges(
          (prev) =>
            patchGraphActiveHighlight(
              [],
              prev,
              lastMessagingHighlightRef.current,
            ).edges,
        )
        scheduleMessagingHighlightTtl()
      }

      // With a static id map, the graph never gets rebuilt from topology
      // refetches — skip the refetch entirely. Without one, the graph is
      // reconciled with fresh topology after every event.
      if (!staticIdMapRef.current) {
        scheduleTopologyRefetchRef.current()
      }
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

    const client = createClient(baseUrl)
    let cancelled = false

    const run = async () => {
      setAgenticError(null)
      try {
        const { workflow_instance_id: instanceId } = await instantiateWorkflow(
          client,
          catalogWorkflowName,
        )
        if (cancelled) return
        const pathUuid = instanceIdToPathUuid(instanceId)
        const inst = await getWorkflowInstanceState(
          client,
          catalogWorkflowName,
          pathUuid,
          true,
        )
        if (cancelled) return
        applyInstanceTopologyRef.current(inst.topology)

        if (cancelled) return
        const session: Session = {
          client,
          baseUrl,
          workflowName: catalogWorkflowName,
          instanceId,
          pathUuid,
          closeSse: null,
          debounceTimer: null,
          retryTimer: null,
          refetchSeq: 0,
          sseReconnectAttempts: 0,
        }
        sessionRef.current = session
        setWorkflowInstanceId(instanceId)

        const attachSse = (): void => {
          const s = sessionRef.current
          if (!s || s.instanceId !== instanceId || cancelled) return
          if (s.closeSse) {
            s.closeSse()
            s.closeSse = null
          }
          if (cancelled) return
          const close = subscribeWorkflowInstanceSse(
            s.baseUrl,
            s.workflowName,
            s.pathUuid,
            (ev: EventV1Wire) => {
              handleWorkflowInstanceSseEventRef.current(
                ev,
                catalogWorkflowName,
                instanceId,
              )
            },
            (err) => {
              logger.apiError("agentic-workflows/sse", err)
              const cur = sessionRef.current
              if (!cur || cur.instanceId !== instanceId || cancelled) return
              if (cur.sseReconnectAttempts >= 6) return
              cur.sseReconnectAttempts += 1
              queueMicrotask(() => {
                attachSse()
              })
            },
          )
          if (cancelled) {
            close()
            return
          }
          if (sessionRef.current?.instanceId === instanceId) {
            sessionRef.current.closeSse = close
          }
        }

        if (cancelled) return
        attachSse()
      } catch (e) {
        if (!cancelled) {
          const msg = e instanceof Error ? e.message : String(e)
          setAgenticError(msg)
          logger.apiError("agentic-workflows/bootstrap", e)
        }
      }
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
