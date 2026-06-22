/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useCallback, useMemo, useRef, useState } from "react"
import type { Node } from "@xyflow/react"
import {
  deleteWorkflowInstance,
  eventTouchesInstance,
  instanceIdToPathUuid,
} from "@/api/agenticWorkflowsClient"
import type { EventV1Wire } from "@/api/agenticWorkflowsTypes"
import { getAgenticWorkflowsApiUrl } from "@/urls"
import { mapWorkflowNameToSlug } from "@/utils/agenticWorkflowsApi"
import { useActiveWorkflowInstanceStore } from "@/stores/activeWorkflowInstanceStore"
import { logger } from "@/utils/logger"
import {
  extractInstanceTopologyFromEvent,
  messagingHighlightIdsFromTopology,
  patchGraphActiveHighlight,
} from "@/utils/workflowEventMessagingHighlight"
import { useWorkflowGraphAgenticBootstrap } from "./useWorkflowGraphAgenticBootstrap"
import { useWorkflowGraphMessagingHighlight } from "./useWorkflowGraphMessagingHighlight"
import { useWorkflowGraphTopologySync } from "./useWorkflowGraphTopologySync"
import type {
  UseWorkflowGraphFromAgenticApiParams,
  UseWorkflowGraphFromAgenticApiResult,
  WorkflowGraphAgenticSession,
} from "./useWorkflowGraphFromAgenticApi.types"

export type {
  UseWorkflowGraphFromAgenticApiParams,
  UseWorkflowGraphFromAgenticApiResult,
} from "./useWorkflowGraphFromAgenticApi.types"

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
  const workflowInstanceId = useActiveWorkflowInstanceStore(
    (s) => s.workflowInstanceId,
  )
  const setWorkflowInstanceId = useActiveWorkflowInstanceStore(
    (s) => s.setWorkflowInstanceId,
  )
  const sessionRef = useRef<WorkflowGraphAgenticSession | null>(null)

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

  const {
    lastMessagingHighlightRef,
    restoreEdgeAnimation,
    resetMessagingHighlightState,
    scheduleMessagingHighlightTtl,
  } = useWorkflowGraphMessagingHighlight(setNodes, setEdges)

  const { applyInstanceTopologyRef, scheduleTopologyRefetchRef } =
    useWorkflowGraphTopologySync({
      patternRef,
      sessionRef,
      onAppliedRef,
      attachHandlers,
      setNodes,
      setEdges,
      restoreEdgeAnimation,
    })

  const clearSession = useCallback(() => {
    const s = sessionRef.current
    if (!s) return
    if (s.closeSse) s.closeSse()
    if (s.debounceTimer) clearTimeout(s.debounceTimer)
    if (s.retryTimer) clearTimeout(s.retryTimer)
    if (s.sseReconnectTimer) clearTimeout(s.sseReconnectTimer)
    const { client, workflowName, instanceId } = s
    sessionRef.current = null
    try {
      const pathUuid = instanceIdToPathUuid(instanceId)
      void deleteWorkflowInstance(client, workflowName, pathUuid).catch(
        (err) => {
          logger.apiError("agentic-workflows/delete-instance", err)
        },
      )
    } catch (err) {
      logger.apiError("agentic-workflows/teardown-invalid-instance-id", err)
    }
    setWorkflowInstanceId(null)
    resetMessagingHighlightState()
  }, [resetMessagingHighlightState, setWorkflowInstanceId])

  const clearSessionRef = useRef(clearSession)
  clearSessionRef.current = clearSession

  const handleWorkflowInstanceSseEvent = useCallback(
    (ev: EventV1Wire, catalogWorkflowName: string, instanceId: string) => {
      if (!eventTouchesInstance(ev, catalogWorkflowName, instanceId)) return

      const partial = extractInstanceTopologyFromEvent(
        ev,
        catalogWorkflowName,
        instanceId,
      )
      const ids = messagingHighlightIdsFromTopology(partial)
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

      scheduleTopologyRefetchRef.current()
    },
    [
      lastMessagingHighlightRef,
      scheduleMessagingHighlightTtl,
      scheduleTopologyRefetchRef,
      setEdges,
      setNodes,
    ],
  )

  const handleWorkflowInstanceSseEventRef = useRef(
    handleWorkflowInstanceSseEvent,
  )
  handleWorkflowInstanceSseEventRef.current = handleWorkflowInstanceSseEvent

  useWorkflowGraphAgenticBootstrap({
    agenticMode,
    baseUrl,
    catalogWorkflowName: selectedWorkflowSummary?.name,
    sessionRef,
    applyInstanceTopologyRef,
    handleWorkflowInstanceSseEventRef,
    clearSessionRef,
    setAgenticError,
    setWorkflowInstanceId,
  })

  return {
    agenticMode,
    agenticError,
    workflowInstanceId,
  }
}
