/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import type { Edge, Node } from "@xyflow/react"
import type { Dispatch, RefObject, SetStateAction } from "react"
import {
  createClient,
  eventTouchesInstance,
  getWorkflowInstanceState,
  instanceIdToPathUuid,
  instantiateWorkflow,
  subscribeWorkflowInstanceSse,
} from "@/api/agenticWorkflowsClient"
import type { EventV1Wire, TopologyWire } from "@/api/agenticWorkflowsTypes"
import { logger } from "@/utils/logger"
import type { StaticIdMap } from "@/utils/topologyStaticIdMap"
import {
  extractInstanceTopologyFromEvent,
  messagingHighlightIdsFromTopology,
  patchGraphActiveHighlight,
  staticGraphHighlightIdsFromTopology,
  type MessagingHighlightIds,
} from "@/utils/workflowEventMessagingHighlight"

export const REFETCH_DEBOUNCE_MS = 80

export interface AgenticWorkflowSession {
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

/** Stable ref bundle passed from the hook into session helpers */
export interface WorkflowGraphAgenticSessionContext {
  sessionRef: RefObject<AgenticWorkflowSession | null>
  staticIdMapRef: RefObject<StaticIdMap | null>
  lastMessagingHighlightRef: RefObject<MessagingHighlightIds>
  applyWorkflowTopologyToGraphRef: RefObject<
    (topology: TopologyWire | undefined) => void
  >
  refetchWorkflowInstanceTopologyRef: RefObject<
    (seq: number, attempt: number) => Promise<void>
  >
  scheduleWorkflowInstanceTopologyRefetchRef: RefObject<() => void>
}

export async function refetchWorkflowInstanceTopologyFromApi(
  context: WorkflowGraphAgenticSessionContext,
  seq: number,
  attempt: number,
): Promise<void> {
  const latest = context.sessionRef.current
  if (!latest || latest.refetchSeq !== seq) return
  try {
    const path = instanceIdToPathUuid(latest.instanceId)
    const fresh = await getWorkflowInstanceState(
      latest.client,
      latest.workflowName,
      path,
      true,
    )
    const stillLatest = context.sessionRef.current
    if (!stillLatest || stillLatest.refetchSeq !== seq) return
    context.applyWorkflowTopologyToGraphRef.current(fresh.topology)
  } catch (e) {
    logger.apiError("agentic-workflows/refetch-topology", e)
    const s = context.sessionRef.current
    if (!s || s.refetchSeq !== seq) return
    if (attempt >= 2) return
    const backoffMs = attempt === 0 ? 200 : 500
    if (s.retryTimer) clearTimeout(s.retryTimer)
    s.retryTimer = setTimeout(() => {
      const current = context.sessionRef.current
      if (current) current.retryTimer = null
      if (!current || current.refetchSeq !== seq) return
      void context.refetchWorkflowInstanceTopologyRef.current(seq, attempt + 1)
    }, backoffMs)
  }
}

export function scheduleDebouncedWorkflowInstanceTopologyRefetch(
  context: WorkflowGraphAgenticSessionContext,
): void {
  const s = context.sessionRef.current
  if (!s) return
  s.refetchSeq += 1
  const seq = s.refetchSeq
  if (s.debounceTimer) clearTimeout(s.debounceTimer)
  if (s.retryTimer) {
    clearTimeout(s.retryTimer)
    s.retryTimer = null
  }
  s.debounceTimer = setTimeout(() => {
    const latest = context.sessionRef.current
    if (!latest || latest.refetchSeq !== seq) return
    latest.debounceTimer = null
    void context.refetchWorkflowInstanceTopologyRef.current(seq, 0)
  }, REFETCH_DEBOUNCE_MS)
}

export function handleAgenticWorkflowInstanceSseEvent(
  context: WorkflowGraphAgenticSessionContext,
  setNodes: Dispatch<SetStateAction<Node[]>>,
  setEdges: Dispatch<SetStateAction<Edge[]>>,
  scheduleMessagingHighlightTtl: () => void,
  ev: EventV1Wire,
  catalogWorkflowName: string,
  instanceId: string,
): void {
  if (!eventTouchesInstance(ev, catalogWorkflowName, instanceId)) return

  const partial = extractInstanceTopologyFromEvent(
    ev,
    catalogWorkflowName,
    instanceId,
  )
  const idMap = context.staticIdMapRef.current
  let ids: MessagingHighlightIds
  if (idMap) {
    ids = staticGraphHighlightIdsFromTopology(partial, idMap)
  } else {
    ids = messagingHighlightIdsFromTopology(partial)
  }
  const hasAny = ids.nodeIds.size > 0 || ids.edgeIds.size > 0
  if (hasAny) {
    context.lastMessagingHighlightRef.current = {
      nodeIds: new Set(ids.nodeIds),
      edgeIds: new Set(ids.edgeIds),
      edgePairs: new Set(ids.edgePairs),
    }
    setNodes(
      (prev) =>
        patchGraphActiveHighlight(
          prev,
          [],
          context.lastMessagingHighlightRef.current,
        ).nodes,
    )
    setEdges(
      (prev) =>
        patchGraphActiveHighlight(
          [],
          prev,
          context.lastMessagingHighlightRef.current,
        ).edges,
    )
    scheduleMessagingHighlightTtl()
  }

  if (!context.staticIdMapRef.current) {
    context.scheduleWorkflowInstanceTopologyRefetchRef.current()
  }
}

export interface BootstrapAgenticWorkflowGraphParams {
  baseUrl: string
  catalogWorkflowName: string
  isCancelled: () => boolean
  sessionRef: RefObject<AgenticWorkflowSession | null>
  applyWorkflowTopologyToGraph: (topology: TopologyWire | undefined) => void
  setWorkflowInstanceId: (id: string | null) => void
  setAgenticError: (message: string) => void
  onSseEvent: (
    ev: EventV1Wire,
    catalogWorkflowName: string,
    instanceId: string,
  ) => void
}

export async function bootstrapAgenticWorkflowGraph(
  params: BootstrapAgenticWorkflowGraphParams,
): Promise<void> {
  const {
    baseUrl,
    catalogWorkflowName,
    isCancelled,
    sessionRef,
    applyWorkflowTopologyToGraph,
    setWorkflowInstanceId,
    setAgenticError,
    onSseEvent,
  } = params

  const client = createClient(baseUrl)
  try {
    const { workflow_instance_id: instanceId } = await instantiateWorkflow(
      client,
      catalogWorkflowName,
    )
    if (isCancelled()) return
    const pathUuid = instanceIdToPathUuid(instanceId)
    const inst = await getWorkflowInstanceState(
      client,
      catalogWorkflowName,
      pathUuid,
      true,
    )
    if (isCancelled()) return
    applyWorkflowTopologyToGraph(inst.topology)

    if (isCancelled()) return
    const session: AgenticWorkflowSession = {
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
      if (!s || s.instanceId !== instanceId || isCancelled())
        return
      if (s.closeSse) {
        s.closeSse()
        s.closeSse = null
      }
      if (isCancelled()) return
      const close = subscribeWorkflowInstanceSse(
        s.baseUrl,
        s.workflowName,
        s.pathUuid,
        (ev: EventV1Wire) => {
          onSseEvent(ev, catalogWorkflowName, instanceId)
        },
        (err) => {
          logger.apiError("agentic-workflows/sse", err)
          const cur = sessionRef.current
          if (
            !cur ||
            cur.instanceId !== instanceId ||
            isCancelled()
          )
            return
          if (cur.sseReconnectAttempts >= 6) return
          cur.sseReconnectAttempts += 1
          queueMicrotask(() => {
            attachSse()
          })
        },
      )
      if (isCancelled()) {
        close()
        return
      }
      if (sessionRef.current?.instanceId === instanceId) {
        sessionRef.current.closeSse = close
      }
    }

    if (isCancelled()) return
    attachSse()
  } catch (e) {
    if (!isCancelled()) {
      const msg = e instanceof Error ? e.message : String(e)
      setAgenticError(msg)
      logger.apiError("agentic-workflows/bootstrap", e)
    }
  }
}
