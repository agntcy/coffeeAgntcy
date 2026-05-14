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
import { identityUiVariantForPattern } from "@/utils/agenticTopologyIdentityUiMap"
import { topologyWireToReactFlow } from "@/utils/topologyToReactFlow"
import {
  extractInstanceTopologyFromEvent,
  messagingHighlightIdsFromTopology,
  patchGraphActiveHighlight,
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

  const [agenticError, setAgenticError] = useState<string | null>(null)
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

  const reapplyMessagingHighlight = useCallback(() => {
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
      // #region agent log
      fetch(
        "http://127.0.0.1:7912/ingest/20932a06-6c8a-43ef-ade1-d12165c38237",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Debug-Session-Id": "d269ae",
          },
          body: JSON.stringify({
            sessionId: "d269ae",
            location: "useWorkflowGraphFromAgenticApi.ts:applyInstanceTopology",
            message: "topology_applied",
            data: {
              mappedNodes: mappedNodes.length,
              mappedEdges: mappedEdges.length,
            },
            timestamp: Date.now(),
            hypothesisId: "H5",
          }),
        },
      ).catch(() => {})
      // #endregion
      onAppliedRef.current?.()
      queueMicrotask(() => {
        reapplyMessagingHighlight()
      })
    },
    [attachHandlers, setNodes, setEdges, reapplyMessagingHighlight],
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
    clearMessagingHighlightTtl()
    lastMessagingHighlightRef.current = {
      nodeIds: new Set(),
      edgeIds: new Set(),
    }
  }, [clearMessagingHighlightTtl])

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
      const wfMap = ev.data?.workflows
      const wfKeys =
        wfMap && typeof wfMap === "object" ? Object.keys(wfMap as object) : []
      const wfBlock =
        wfMap && typeof wfMap === "object"
          ? (wfMap as Record<string, { instances?: unknown }>)[
              catalogWorkflowName
            ]
          : undefined
      const instRaw = wfBlock?.instances
      const instKeys =
        instRaw && typeof instRaw === "object"
          ? Object.keys(instRaw as object)
          : []
      const touches = eventTouchesInstance(ev, catalogWorkflowName, instanceId)
      // #region agent log
      fetch(
        "http://127.0.0.1:7912/ingest/20932a06-6c8a-43ef-ade1-d12165c38237",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Debug-Session-Id": "d269ae",
          },
          body: JSON.stringify({
            sessionId: "d269ae",
            location:
              "useWorkflowGraphFromAgenticApi.ts:handleWorkflowInstanceSseEvent",
            message: "sse_event_received",
            data: {
              metaType: ev.metadata?.type,
              wfKeyCount: wfKeys.length,
              hasCatalogWfKey: wfKeys.includes(catalogWorkflowName),
              instKeyCount: instKeys.length,
              instKeyMatchesExpected: instKeys.includes(instanceId),
              instKey0Tail:
                instKeys[0] != null ? String(instKeys[0]).slice(-12) : null,
              expectedIdTail: instanceId.slice(-12),
              touches,
            },
            timestamp: Date.now(),
            hypothesisId: "H2",
          }),
        },
      ).catch(() => {})
      // #endregion
      if (!touches) return

      const partial = extractInstanceTopologyFromEvent(
        ev,
        catalogWorkflowName,
        instanceId,
      )
      const ids = messagingHighlightIdsFromTopology(partial)
      const hasAny = ids.nodeIds.size > 0 || ids.edgeIds.size > 0
      const graphIds = lastAppliedGraphNodeIdsRef.current
      let hlNodesOnGraph = 0
      for (const id of ids.nodeIds) {
        if (graphIds.has(id)) hlNodesOnGraph++
      }
      // #region agent log
      fetch(
        "http://127.0.0.1:7912/ingest/20932a06-6c8a-43ef-ade1-d12165c38237",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Debug-Session-Id": "d269ae",
          },
          body: JSON.stringify({
            sessionId: "d269ae",
            location:
              "useWorkflowGraphFromAgenticApi.ts:handleWorkflowInstanceSseEvent",
            message: "topology_fragment_for_highlight",
            data: {
              hasPartial: partial != null,
              highlightNodeCount: ids.nodeIds.size,
              highlightEdgeCount: ids.edgeIds.size,
              hasAny,
              graphNodeCount: graphIds.size,
              hlNodesOnGraph,
              sampleHlNodeTail:
                [...ids.nodeIds][0] != null
                  ? String([...ids.nodeIds][0]).slice(-16)
                  : null,
            },
            timestamp: Date.now(),
            hypothesisId: "H3-H4",
          }),
        },
      ).catch(() => {})
      // #endregion
      if (hasAny) {
        lastMessagingHighlightRef.current = {
          nodeIds: new Set(ids.nodeIds),
          edgeIds: new Set(ids.edgeIds),
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
        // #region agent log
        fetch(
          "http://127.0.0.1:7912/ingest/20932a06-6c8a-43ef-ade1-d12165c38237",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-Debug-Session-Id": "d269ae",
            },
            body: JSON.stringify({
              sessionId: "d269ae",
              location:
                "useWorkflowGraphFromAgenticApi.ts:handleWorkflowInstanceSseEvent",
              message: "highlight_patch_scheduled",
              data: {
                hlNodeCount: lastMessagingHighlightRef.current.nodeIds.size,
                hlEdgeCount: lastMessagingHighlightRef.current.edgeIds.size,
              },
              timestamp: Date.now(),
              hypothesisId: "H4",
            }),
          },
        ).catch(() => {})
        // #endregion
      }

      scheduleTopologyRefetchRef.current()
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
              // #region agent log
              fetch(
                "http://127.0.0.1:7912/ingest/20932a06-6c8a-43ef-ade1-d12165c38237",
                {
                  method: "POST",
                  headers: {
                    "Content-Type": "application/json",
                    "X-Debug-Session-Id": "d269ae",
                  },
                  body: JSON.stringify({
                    sessionId: "d269ae",
                    location: "useWorkflowGraphFromAgenticApi.ts:attachSse",
                    message: "sse_reconnect_scheduled",
                    data: { attempt: cur.sseReconnectAttempts },
                    timestamp: Date.now(),
                    hypothesisId: "H6",
                  }),
                },
              ).catch(() => {})
              // #endregion
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
        // #region agent log
        fetch(
          "http://127.0.0.1:7912/ingest/20932a06-6c8a-43ef-ade1-d12165c38237",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-Debug-Session-Id": "d269ae",
            },
            body: JSON.stringify({
              sessionId: "d269ae",
              location: "useWorkflowGraphFromAgenticApi.ts:bootstrap",
              message: "sse_subscribed",
              data: {
                wf: catalogWorkflowName,
                pathUuidTail: pathUuid.slice(-8),
              },
              timestamp: Date.now(),
              hypothesisId: "H0",
            }),
          },
        ).catch(() => {})
        // #endregion
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
  }, [agenticMode, baseUrl, selectedWorkflowSummary?.name])

  return { agenticMode, agenticError }
}
