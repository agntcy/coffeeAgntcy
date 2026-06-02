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
import { useWorkflowGraphFromAgenticApi } from "@/hooks/useWorkflowGraphFromAgenticApi"
import type { WorkflowSummary } from "@/utils/agenticWorkflowsApi"
import type { GraphConfig } from "@/utils/graphConfigs"
import { graphConfigFromNodes } from "@/utils/graphConfigFromNodes"
import { logger } from "@/utils/logger"

export interface MainAreaProps {
  pattern: PatternType
  selectedWorkflowSummary: WorkflowSummary | null
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
  /** Latest graph snapshot for chat/feeds (GroupCommunication sender map). */
  onLiveGraphConfig?: (config: GraphConfig) => void
}

const DELAY_DURATION = 500
const HIGHLIGHT = { ON: true, OFF: false } as const

export function useMainArea({
  pattern,
  selectedWorkflowSummary,
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
  onLiveGraphConfig,
}: MainAreaProps) {
  const fitViewWithViewport = useViewportAwareFitView()
  const isGroupCommConnected =
    pattern !== "group_messaging" || groupCommResponseReceived
  const config = useMemo(() => getGraphConfig(pattern), [pattern])

  const [nodesDraggable, setNodesDraggable] = useState(true)
  const [nodesConnectable, setNodesConnectable] = useState(true)

  const {
    activeModal,
    activeNodeData,
    handleOpenIdentityModal,
    handleCloseModals,
    handleShowBadgeDetails,
    handleShowPolicyDetails,
    handlePaneClick: modalPaneClick,
  } = useModalManager()
  const [oasfModalOpen, setOasfModalOpen] = useState(false)
  const [oasfModalData, setOasfModalData] = useState<CustomNodeData | null>(
    null,
  )

  const [nodes, setNodes, onNodesChange] = useNodesState(config.nodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(config.edges)
  const animationLock = useRef<boolean>(false)

  const handleOpenOasfModal = useCallback((nodeData: CustomNodeData) => {
    setOasfModalData(nodeData)
    setOasfModalOpen(true)
  }, [])

  const { agenticMode, agenticError, staticIdMapActive, restoreEdgeAnimation } =
    useWorkflowGraphFromAgenticApi({
      pattern,
      selectedWorkflowSummary,
      setNodes,
      setEdges,
      handleOpenIdentityModal,
      handleOpenOasfModal,
      onTopologyApplied: () => {
        setTimeout(() => {
          fitViewWithViewport()
        }, 200)
      },
    })

  useEffect(() => {
    if (!agenticError) return
    logger.error("agentic-workflows/graph-session", { detail: agenticError })
  }, [agenticError])

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
    if (pattern !== "a2a_http") return
    setNodes((prevNodes) => {
      const recruiterId =
        prevNodes.find((n) => {
          const l1 = String(
            (n.data as unknown as CustomNodeData | undefined)?.label1 ?? "",
          )
            .toLowerCase()
            .trim()
          return l1.includes("recruiter")
        })?.id ?? NODE_IDS.RECRUITER
      return prevNodes.map((node) => {
        const nodeData = node.data as unknown as CustomNodeData | undefined
        const shouldBeSelected =
          selectedAgentCid != null
            ? nodeData?.agentCid === selectedAgentCid
            : node.id === recruiterId
        if (nodeData?.selected === shouldBeSelected) return node
        return { ...node, data: { ...node.data, selected: shouldBeSelected } }
      })
    })
  }, [pattern, selectedAgentCid, nodeAgentCidKey, setNodes])

  useMainAreaGraphEffects({
    pattern,
    skipStaticGraphSync: agenticMode && !staticIdMapActive,
    restoreEdgeAnimation: staticIdMapActive ? restoreEdgeAnimation : undefined,
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
    if (agenticMode) return
    if (pattern === "group_messaging") return
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
    agenticMode,
  ])

  useEffect(() => {
    if (!onLiveGraphConfig) return
    const title =
      agenticMode && selectedWorkflowSummary
        ? `${selectedWorkflowSummary.name} — ${selectedWorkflowSummary.scenario}`
        : config.title
    onLiveGraphConfig(
      graphConfigFromNodes(
        title,
        nodes,
        edges,
        agenticMode ? [] : config.animationSequence,
      ),
    )
  }, [
    onLiveGraphConfig,
    agenticMode,
    pattern,
    selectedWorkflowSummary,
    config.title,
    config.animationSequence,
    nodes,
    edges,
  ])

  const highlightNode = useCallback(
    (nodeId: string) => {
      if (!nodeId) return
      if (pattern === "group_messaging") {
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
    handleCloseModals,
    handleShowBadgeDetails,
    handleShowPolicyDetails,
    oasfModalOpen,
    setOasfModalOpen,
    oasfModalData,
    onPaneClick,
    onNodeDrag,
  }
}
