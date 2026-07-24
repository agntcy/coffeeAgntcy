/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useCallback, useRef } from "react"
import type { Edge, Node } from "@xyflow/react"
import {
  patchGraphActiveHighlight,
  type MessagingHighlightIds,
} from "@/utils/workflowEventMessagingHighlight"
import { MESSAGING_HIGHLIGHT_TTL_MS } from "./useWorkflowGraphFromAgenticApi.types"

export function useWorkflowGraphMessagingHighlight(
  setNodes: React.Dispatch<React.SetStateAction<Node[]>>,
  setEdges: React.Dispatch<React.SetStateAction<Edge[]>>,
) {
  const lastMessagingHighlightRef = useRef<MessagingHighlightIds>({
    nodeIds: new Set(),
    edgeIds: new Set(),
    edgePairs: new Set(),
  })
  const highlightTtlTimerRef = useRef<ReturnType<typeof setTimeout> | null>(
    null,
  )

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

  const resetMessagingHighlightState = useCallback(() => {
    clearMessagingHighlightTtl()
    lastMessagingHighlightRef.current = {
      nodeIds: new Set(),
      edgeIds: new Set(),
      edgePairs: new Set(),
    }
  }, [clearMessagingHighlightTtl])

  return {
    lastMessagingHighlightRef,
    restoreEdgeAnimation,
    clearMessagingHighlightTtl,
    scheduleMessagingHighlightTtl,
    resetMessagingHighlightState,
  }
}
