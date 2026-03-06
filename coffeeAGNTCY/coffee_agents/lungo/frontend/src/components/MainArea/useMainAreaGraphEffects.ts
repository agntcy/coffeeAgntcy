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
}

/** Runs effects that sync graph config, viewport, transport labels, tooltips, and edge checks. */
export function useMainAreaGraphEffects({
  pattern,
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
}: UseMainAreaGraphEffectsParams) {
  useEffect(() => {
    animationLockRef.current = false
  }, [pattern, animationLockRef])

  useEffect(() => {
    handleCloseModals()
    setOasfModalOpen(false)
  }, [pattern, handleCloseModals, setOasfModalOpen])

  useEffect(() => {
    setNodes((nodes) =>
      nodes.map((node) => ({
        ...node,
        data: { ...node.data, active: false },
      })),
    )
    setEdges([])
  }, [pattern, setNodes, setEdges])

  useEffect(() => {
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
  ])

  useEffect(() => {
    const handleVisibilityChange = async () => {
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
  }, [pattern, setNodes, setEdges])

  useEffect(() => {
    fitViewWithViewport({ chatHeight, isExpanded })
  }, [chatHeight, isExpanded, fitViewWithViewport])

  useEffect(() => {
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
  }, [config.edges, setEdges, animationLockRef])

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
