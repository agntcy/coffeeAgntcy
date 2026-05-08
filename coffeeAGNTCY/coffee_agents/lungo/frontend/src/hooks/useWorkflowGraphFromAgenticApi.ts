/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useCallback, useEffect, useRef, useState } from "react"
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
import { topologyWireToReactFlow } from "@/utils/topologyToReactFlow"

const REFETCH_DEBOUNCE_MS = 80

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
  const baseUrl = getAgenticWorkflowsApiUrl().replace(/\/$/, "")
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
    closeSse: (() => void) | null
    debounceTimer: ReturnType<typeof setTimeout> | null
    retryTimer: ReturnType<typeof setTimeout> | null
    refetchSeq: number
  }
  const sessionRef = useRef<Session | null>(null)

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

  const applyInstanceTopology = useCallback(
    (
      topology: import("@/api/agenticWorkflowsTypes").TopologyWire | undefined,
    ) => {
      const { nodes: mappedNodes, edges: mappedEdges } =
        topologyWireToReactFlow(topology)
      const withHandlers = mappedNodes.map(attachHandlers)
      setNodes((prev) => mergeDiscoveryNodes(withHandlers, prev))
      setEdges((prev) => mergeDiscoveryEdges(mappedEdges, prev))
      onAppliedRef.current?.()
    },
    [attachHandlers, setNodes, setEdges],
  )

  const clearSession = useCallback(() => {
    const s = sessionRef.current
    if (!s) return
    if (s.closeSse) s.closeSse()
    if (s.debounceTimer) clearTimeout(s.debounceTimer)
    if (s.retryTimer) clearTimeout(s.retryTimer)
    sessionRef.current = null
  }, [])

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
        applyInstanceTopology(fresh.topology)
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
          void refetchAndApplyTopology(seq, attempt + 1)
        }, backoffMs)
      }
    },
    [applyInstanceTopology],
  )

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
      void refetchAndApplyTopology(seq, 0)
    }, REFETCH_DEBOUNCE_MS)
  }, [refetchAndApplyTopology])

  useEffect(() => {
    if (!agenticMode || !baseUrl || !workflowName) {
      clearSession()
      setAgenticError(null)
      return
    }

    clearSession()

    const client = createClient(baseUrl)
    let cancelled = false

    const run = async () => {
      setAgenticError(null)
      try {
        const { workflow_instance_id: instanceId } = await instantiateWorkflow(
          client,
          workflowName,
        )
        if (cancelled) return
        const pathUuid = instanceIdToPathUuid(instanceId)
        const inst = await getWorkflowInstanceState(
          client,
          workflowName,
          pathUuid,
          true,
        )
        if (cancelled) return
        applyInstanceTopology(inst.topology)

        const session: Session = {
          client,
          baseUrl,
          workflowName,
          instanceId,
          closeSse: null,
          debounceTimer: null,
          retryTimer: null,
          refetchSeq: 0,
        }
        sessionRef.current = session

        const close = subscribeWorkflowInstanceSse(
          baseUrl,
          workflowName,
          pathUuid,
          (ev: EventV1Wire) => {
            if (!eventTouchesInstance(ev, workflowName, instanceId)) return
            scheduleTopologyRefetch()
          },
          (err) => {
            logger.apiError("agentic-workflows/sse", err)
          },
        )
        if (sessionRef.current) sessionRef.current.closeSse = close
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
      clearSession()
    }
  }, [
    agenticMode,
    baseUrl,
    workflowName,
    selectedWorkflowSummary,
    applyInstanceTopology,
    pattern,
    attachHandlers,
    setNodes,
    setEdges,
    clearSession,
    scheduleTopologyRefetch,
    refetchAndApplyTopology,
  ])

  return { agenticMode, agenticError }
}
