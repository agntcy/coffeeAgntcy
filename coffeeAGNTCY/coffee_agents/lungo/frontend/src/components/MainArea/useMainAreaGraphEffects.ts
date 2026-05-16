/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useEffect } from "react"
import type { Node, Edge } from "@xyflow/react"
import { getGraphConfig, updateTransportLabels } from "@/utils/graphConfigs"
import {
  isStreamingPattern,
  supportsTransportUpdates,
} from "@/utils/patternUtils"
import type { GraphConfig } from "@/utils/graphConfigs"
import type { CustomNodeData } from "./Graph/Elements/types"

export interface UseMainAreaGraphEffectsParams {
  pattern: string
  /** When true, skip syncing from `getGraphConfig` (graph owned by Agentic Workflows API). */
  skipStaticGraphSync?: boolean
  isGroupCommConnected: boolean
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
  activeModal: string | null
  activeNodeData: unknown
  fitViewWithViewport: (opts: {
    chatHeight: number
    isExpanded: boolean
  }) => void
  chatHeight: number
  isExpanded: boolean
  config: GraphConfig
  animationLockRef: React.MutableRefObject<boolean>
  nodesDraggable: boolean
  nodesConnectable: boolean
  handleCloseModals: () => void
  setOasfModalOpen: (open: boolean) => void
  /**
   * Optional callback invoked after any full graph rebuild from
   * `getGraphConfig` so the SSE-driven highlight (`data.active` +
   * `edge.animated`) can be re-applied to the freshly-built nodes/edges.
   * Used when a static overlay is active so the highlight survives effects
   * that rebuild the static graph.
   */
  reapplyMessagingHighlight?: () => void
}

/** Runs effects that sync graph config, viewport, transport labels, tooltips, and edge checks. */
export function useMainAreaGraphEffects({
  pattern,
  skipStaticGraphSync = false,
  isGroupCommConnected,
  setNodes,
  setEdges,
  handleOpenIdentityModal,
  handleOpenOasfModal,
  activeModal,
  activeNodeData,
  fitViewWithViewport,
  chatHeight,
  isExpanded,
  config,
  animationLockRef,
  nodesDraggable,
  nodesConnectable,
  handleCloseModals,
  setOasfModalOpen,
  reapplyMessagingHighlight,
}: UseMainAreaGraphEffectsParams) {
  useEffect(() => {
    animationLockRef.current = false
  }, [pattern, animationLockRef])

  useEffect(() => {
    handleCloseModals()
    setOasfModalOpen(false)
  }, [pattern, handleCloseModals, setOasfModalOpen])

  useEffect(() => {
    if (skipStaticGraphSync) return
    setNodes((nodes) =>
      nodes.map((node) => ({
        ...node,
        data: { ...node.data, active: false },
      })),
    )
    setEdges([])
    // After clearing edges (and any node `active` state), restore the
    // current SSE highlight so the messaging-path animation isn't lost on
    // pattern change. Call synchronously so the reapply's functional
    // updates layer on top of the cleared state in the same React batch
    // (a microtask hop here can race the static rebuild below).
    if (reapplyMessagingHighlight) {
      reapplyMessagingHighlight()
    }
  }, [pattern, setNodes, setEdges, skipStaticGraphSync, reapplyMessagingHighlight])

  useEffect(() => {
    if (!skipStaticGraphSync) return
    setNodes((nodes) =>
      nodes.map((node) => ({
        ...node,
        data: {
          ...node.data,
          onOpenIdentityModal: handleOpenIdentityModal,
          onOpenOasfModal: handleOpenOasfModal,
          isModalOpen: !!(
            activeModal &&
            (activeNodeData as { id?: string } | null)?.id === node.id
          ),
        },
      })),
    )
  }, [
    skipStaticGraphSync,
    handleOpenIdentityModal,
    handleOpenOasfModal,
    activeModal,
    activeNodeData,
    setNodes,
  ])

  useEffect(() => {
    if (skipStaticGraphSync) return
    const updateGraph = async () => {
      const newConfig = getGraphConfig(pattern)
      const nodesWithHandlers = newConfig.nodes.map((node) => ({
        ...node,
        data: {
          ...node.data,
          onOpenIdentityModal: handleOpenIdentityModal,
          onOpenOasfModal: handleOpenOasfModal,
          isModalOpen: !!(
            activeModal &&
            (activeNodeData as { id?: string } | null)?.id === node.id
          ),
        },
      }))
      setNodes(nodesWithHandlers)
      await new Promise((resolve) => setTimeout(resolve, 100))
      setEdges(newConfig.edges)
      await updateTransportLabels(
        setNodes,
        setEdges,
        pattern,
        isStreamingPattern(pattern),
      )
      // The full rebuild above wipes `data.active` and resets edges; if
      // an SSE highlight was active, restore it on the rebuilt graph.
      // Synchronous (not queueMicrotask) so the reapply's functional
      // setNodes/setEdges layer on top of the rebuild deterministically.
      if (reapplyMessagingHighlight) {
        reapplyMessagingHighlight()
      }
      setTimeout(() => {
        fitViewWithViewport({ chatHeight: 0, isExpanded: false })
      }, 200)
    }
    updateGraph()
  }, [
    fitViewWithViewport,
    pattern,
    isGroupCommConnected,
    setNodes,
    setEdges,
    handleOpenIdentityModal,
    activeModal,
    activeNodeData,
    handleOpenOasfModal,
    skipStaticGraphSync,
    reapplyMessagingHighlight,
  ])

  useEffect(() => {
    const handleVisibilityChange = async () => {
      if (skipStaticGraphSync) return
      if (!document.hidden && supportsTransportUpdates(pattern)) {
        await updateTransportLabels(
          setNodes,
          setEdges,
          pattern,
          isStreamingPattern(pattern),
        )
      }
    }
    document.addEventListener("visibilitychange", handleVisibilityChange)
    return () =>
      document.removeEventListener("visibilitychange", handleVisibilityChange)
  }, [pattern, setNodes, setEdges, skipStaticGraphSync])

  useEffect(() => {
    fitViewWithViewport({ chatHeight, isExpanded })
  }, [chatHeight, isExpanded, fitViewWithViewport])

  useEffect(() => {
    if (skipStaticGraphSync) return
    const checkEdges = () => {
      const expectedEdges = config.edges.length
      const renderedEdges =
        document.querySelectorAll(".react-flow__edge").length
      if (
        expectedEdges > 0 &&
        renderedEdges === 0 &&
        !animationLockRef.current
      ) {
        setEdges([])
        setTimeout(() => setEdges(config.edges), 100)
      }
    }
    const intervalId = setInterval(checkEdges, 2000)
    const timeoutId = setTimeout(checkEdges, 1000)
    return () => {
      clearInterval(intervalId)
      clearTimeout(timeoutId)
    }
  }, [config.edges, setEdges, animationLockRef, skipStaticGraphSync])

  useEffect(() => {
    const addTooltips = () => {
      const controlButtons = document.querySelectorAll(
        ".react-flow__controls-button",
      )
      const tooltips = ["Zoom In", "Zoom Out", "Fit View", "Lock"]
      controlButtons.forEach((button, index) => {
        if (index < tooltips.length) {
          if (index === 3) {
            const isLocked = !nodesDraggable || !nodesConnectable
            button.setAttribute("data-tooltip", isLocked ? "Unlock" : "Lock")
          } else {
            button.setAttribute("data-tooltip", tooltips[index])
          }
          button.removeAttribute("title")
        }
      })
    }
    const timeoutId = setTimeout(addTooltips, 100)
    return () => clearTimeout(timeoutId)
  }, [pattern, nodesDraggable, nodesConnectable])
}
