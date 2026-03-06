/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useEffect, useRef, useCallback, useState, useMemo } from "react"
import { useNodesState, useEdgesState } from "@xyflow/react"
import { PatternType } from "@/utils/patternUtils"
import { getGraphConfig } from "@/utils/graphConfigs"
import { useViewportAwareFitView } from "@/hooks/useViewportAwareFitView"
import { useModalManager } from "@/hooks/useModalManager"
import { NODE_IDS } from "@/utils/const.ts"
import type { DiscoveryResponseEvent } from "@/types/agent"
import type { CustomNodeData } from "./Graph/Elements/types"
import { useMainAreaDiscoveryGraph } from "./useMainAreaDiscoveryGraph"
import { useMainAreaGraphEffects } from "./useMainAreaGraphEffects"

export interface MainAreaProps {
  pattern: PatternType
  buttonClicked: boolean
  setButtonClicked: (clicked: boolean) => void
  aiReplied: boolean
  setAiReplied: (replied: boolean) => void
  chatHeight?: number
  isExpanded?: boolean
  groupCommResponseReceived?: boolean
  onNodeHighlight?: (highlightFunction: (nodeId: string) => void) => void
  discoveryResponseEvent?: DiscoveryResponseEvent | null
  selectedAgentCid?: string | null
}

const DELAY_DURATION = 500
const HIGHLIGHT = { ON: true, OFF: false } as const

export function useMainArea({
  pattern,
  buttonClicked,
  setButtonClicked,
  aiReplied,
  setAiReplied,
  chatHeight = 0,
  isExpanded = false,
  groupCommResponseReceived = false,
  onNodeHighlight,
  discoveryResponseEvent,
  selectedAgentCid,
}: MainAreaProps) {
  const fitViewWithViewport = useViewportAwareFitView()
  const isGroupCommConnected =
    pattern !== "group_communication" || groupCommResponseReceived
  const config = useMemo(() => getGraphConfig(pattern), [pattern])

  const [nodesDraggable, setNodesDraggable] = useState(true)
  const [nodesConnectable, setNodesConnectable] = useState(true)

  const {
    activeModal,
    activeNodeData,
    modalPosition,
    handleOpenIdentityModal,
    handleCloseModals,
    handleShowBadgeDetails,
    handleShowPolicyDetails,
    handlePaneClick: modalPaneClick,
  } = useModalManager()

  const [nodes, setNodes, onNodesChange] = useNodesState(config.nodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(config.edges)
  const animationLock = useRef<boolean>(false)

  const [oasfModalOpen, setOasfModalOpen] = useState(false)
  const [oasfModalData, setOasfModalData] = useState<CustomNodeData | null>(
    null,
  )
  const [oasfModalPosition, setOasfModalPosition] = useState<{
    x: number
    y: number
  }>({ x: 0, y: 0 })

  const handleOpenOasfModal = useCallback(
    (nodeData: CustomNodeData, position: { x: number; y: number }) => {
      setOasfModalData(nodeData)
      setOasfModalPosition(position)
      setOasfModalOpen(true)
    },
    [],
  )

  useMainAreaDiscoveryGraph({
    pattern,
    discoveryResponseEvent,
    setNodes,
    setEdges,
    handleOpenIdentityModal,
    handleOpenOasfModal,
  })

  const nodeAgentCidKey = useMemo(
    () =>
      nodes
        .filter((n) => (n.data as Record<string, unknown>)?.agentCid)
        .map((n) => `${n.id}:${(n.data as Record<string, unknown>)?.agentCid}`)
        .sort()
        .join(","),
    [nodes],
  )

  useEffect(() => {
    if (pattern !== "on_demand_discovery") return
    setNodes((prevNodes) =>
      prevNodes.map((node) => {
        const nodeData = node.data as unknown as CustomNodeData | undefined
        const shouldBeSelected =
          selectedAgentCid != null
            ? nodeData?.agentCid === selectedAgentCid
            : node.id === NODE_IDS.RECRUITER
        if (nodeData?.selected === shouldBeSelected) return node
        return { ...node, data: { ...node.data, selected: shouldBeSelected } }
      }),
    )
  }, [pattern, selectedAgentCid, nodeAgentCidKey, setNodes])

  useMainAreaGraphEffects({
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
    animationLockRef: animationLock,
    nodesDraggable,
    nodesConnectable,
    handleCloseModals,
    setOasfModalOpen,
  })

  const delay = (ms: number): Promise<void> =>
    new Promise((resolve) => setTimeout(resolve, ms))

  const updateStyle = useCallback(
    (id: string, active: boolean): void => {
      setNodes((nodes) =>
        nodes.map((node) =>
          node.id === id ? { ...node, data: { ...node.data, active } } : node,
        ),
      )
      setTimeout(() => {
        setEdges((edges) =>
          edges.map((edge) =>
            edge.id === id ? { ...edge, data: { ...edge.data, active } } : edge,
          ),
        )
      }, 10)
    },
    [setNodes, setEdges],
  )

  useEffect(() => {
    const shouldAnimate = buttonClicked && !aiReplied
    if (!shouldAnimate) return
    if (pattern === "group_communication") return
    const waitForAnimationAndRun = async () => {
      while (animationLock.current) await delay(100)
      animationLock.current = true
      const animate = async (ids: string[], active: boolean): Promise<void> => {
        ids.forEach((id: string) => updateStyle(id, active))
        await delay(DELAY_DURATION)
      }
      const animateGraph = async (): Promise<void> => {
        const animationSequence = config.animationSequence
        for (const step of animationSequence) {
          await animate(step.ids, HIGHLIGHT.ON)
          await animate(step.ids, HIGHLIGHT.OFF)
        }
        setButtonClicked(false)
        animationLock.current = false
      }
      await animateGraph()
    }
    waitForAnimationAndRun()
  }, [
    buttonClicked,
    setButtonClicked,
    aiReplied,
    setAiReplied,
    pattern,
    updateStyle,
    config.animationSequence,
  ])

  const highlightNode = useCallback(
    (nodeId: string) => {
      if (!nodeId) return
      if (pattern === "group_communication") {
        updateStyle(nodeId, HIGHLIGHT.ON)
        setTimeout(() => updateStyle(nodeId, HIGHLIGHT.OFF), 1800)
      }
    },
    [updateStyle, pattern],
  )

  useEffect(() => {
    if (onNodeHighlight) onNodeHighlight(highlightNode)
  }, [onNodeHighlight, highlightNode])

  const onPaneClick = modalPaneClick
  const onNodeDrag = useCallback(() => {}, [])

  return {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    nodesDraggable,
    setNodesDraggable,
    nodesConnectable,
    setNodesConnectable,
    activeModal,
    activeNodeData,
    modalPosition,
    handleCloseModals,
    handleShowBadgeDetails,
    handleShowPolicyDetails,
    oasfModalOpen,
    setOasfModalOpen,
    oasfModalData,
    oasfModalPosition,
    onPaneClick,
    onNodeDrag,
  }
}
