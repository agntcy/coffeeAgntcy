/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useEffect } from "react"
import type { RefObject } from "react"
import {
  createClient,
  getWorkflowInstanceState,
  instanceIdToPathUuid,
  instantiateWorkflow,
  subscribeWorkflowInstanceSse,
} from "@/api/agenticWorkflowsClient"
import type { EventV1Wire, TopologyWire } from "@/api/agenticWorkflowsTypes"
import { logger } from "@/utils/logger"
import {
  SSE_RECONNECT_BACKOFF_MS,
  type WorkflowGraphAgenticSession,
} from "./useWorkflowGraphFromAgenticApi.types"

interface UseWorkflowGraphAgenticBootstrapParams {
  agenticMode: boolean
  baseUrl: string
  catalogWorkflowName: string | undefined
  sessionRef: RefObject<WorkflowGraphAgenticSession | null>
  applyInstanceTopologyRef: RefObject<
    (topology: TopologyWire | undefined) => void
  >
  handleWorkflowInstanceSseEventRef: RefObject<
    (ev: EventV1Wire, catalogWorkflowName: string, instanceId: string) => void
  >
  clearSessionRef: RefObject<() => void>
  setAgenticError: (error: string | null) => void
  setWorkflowInstanceId: (id: string | null) => void
}

export function useWorkflowGraphAgenticBootstrap({
  agenticMode,
  baseUrl,
  catalogWorkflowName,
  sessionRef,
  applyInstanceTopologyRef,
  handleWorkflowInstanceSseEventRef,
  clearSessionRef,
  setAgenticError,
  setWorkflowInstanceId,
}: UseWorkflowGraphAgenticBootstrapParams): void {
  useEffect(() => {
    const clearSession = clearSessionRef.current

    if (!agenticMode || !baseUrl || !catalogWorkflowName) {
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
        const session: WorkflowGraphAgenticSession = {
          client,
          baseUrl,
          workflowName: catalogWorkflowName,
          instanceId,
          pathUuid,
          closeSse: null,
          debounceTimer: null,
          retryTimer: null,
          sseReconnectTimer: null,
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
              const delayMs =
                SSE_RECONNECT_BACKOFF_MS * cur.sseReconnectAttempts
              if (cur.sseReconnectTimer) clearTimeout(cur.sseReconnectTimer)
              cur.sseReconnectTimer = setTimeout(() => {
                const current = sessionRef.current
                if (current) current.sseReconnectTimer = null
                if (
                  !current ||
                  current.instanceId !== instanceId ||
                  cancelled
                ) {
                  return
                }
                attachSse()
              }, delayMs)
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
      clearSession()
    }
  }, [
    agenticMode,
    applyInstanceTopologyRef,
    baseUrl,
    catalogWorkflowName,
    clearSessionRef,
    handleWorkflowInstanceSseEventRef,
    sessionRef,
    setAgenticError,
    setWorkflowInstanceId,
  ])
}
