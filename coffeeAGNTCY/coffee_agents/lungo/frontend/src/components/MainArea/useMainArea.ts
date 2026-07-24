/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useEffect, useRef, useCallback, useState, useMemo } from "react"
import { useNodesState, useEdgesState } from "@xyflow/react"
import type { Node, Edge } from "@xyflow/react"
import { PatternType } from "@/utils/patternUtils"
import { useViewportAwareFitView } from "@/hooks/useViewportAwareFitView"
import { useModalManager } from "@/hooks/useModalManager"
import { customNodeDataFromNode } from "./Graph/Elements/customNodeData"
import type { CustomNodeData } from "./Graph/Elements/types"
import { useMainAreaGraphEffects } from "./useMainAreaGraphEffects"
import { useWorkflowGraphFromAgenticApi } from "@/hooks/useWorkflowGraphFromAgenticApi"
import { useNodeTransportInterfaces } from "./useNodeTransportInterfaces"
import type { WorkflowSummary } from "@/utils/agenticWorkflowsApi"
import type { GraphConfig } from "@/utils/graphConfigs"
import { graphConfigFromNodes } from "@/utils/graphConfigFromNodes"
import { deriveAnimationSequenceFromGraph } from "@/components/Chat/chatStreamGraphHighlight"
import { logger } from "@/utils/logger"

export interface MainAreaProps {
  pattern: PatternType
  selectedWorkflowSummary: WorkflowSummary | null
  workflowCatalogLoading?: boolean
  workflowCatalogError?: string | null
  buttonClicked: boolean
  setButtonClicked: (clicked: boolean) => void
  aiReplied: boolean
  chatHeight?: number
  isExpanded?: boolean
  groupCommResponseReceived?: boolean
  onNodeHighlight?: (highlightFunction: (nodeId: string) => void) => void
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
  chatHeight = 0,
  isExpanded = false,
  onNodeHighlight,
  selectedAgentCid,
  onLiveGraphConfig,
}: MainAreaProps) {
  const fitViewWithViewport = useViewportAwareFitView()

  const [nodesDraggable, setNodesDraggable] = useState(true)
  const [nodesConnectable, setNodesConnectable] = useState(true)
  const [topologyApplied, setTopologyApplied] = useState(false)
  const [layoutSyncGeneration, setLayoutSyncGeneration] = useState(0)
  const [layoutSyncNodeIds, setLayoutSyncNodeIds] = useState<readonly string[]>(
    [],
  )
  const [layoutSyncFitViewport, setLayoutSyncFitViewport] = useState(false)
  const hasInitialViewportFitRef = useRef(false)

  const {
    activeModal,
    activeNodeId,
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

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])
  const animationLock = useRef<boolean>(false)
  // Latest graph snapshot read at animation start so the agentic button-pulse
  // targets live ids without re-triggering the effect on every node mutation.
  const nodesRef = useRef(nodes)
  const edgesRef = useRef(edges)
  useEffect(() => {
    nodesRef.current = nodes
    edgesRef.current = edges
  }, [nodes, edges])

  const handleOpenOasfModal = useCallback((nodeData: CustomNodeData) => {
    setOasfModalData(nodeData)
    setOasfModalOpen(true)
  }, [])

  const handleLayoutSyncReady = useCallback(() => {
    hasInitialViewportFitRef.current = true
    setTopologyApplied(true)
  }, [])

  const handleTopologyApplied = useCallback((nodeIds: readonly string[]) => {
    setLayoutSyncNodeIds(nodeIds)
    setLayoutSyncFitViewport(!hasInitialViewportFitRef.current)
    setLayoutSyncGeneration((generation) => generation + 1)
  }, [])

  const { agenticMode, agenticError } = useWorkflowGraphFromAgenticApi({
    pattern,
    selectedWorkflowSummary,
    setNodes,
    setEdges,
    handleOpenIdentityModal,
    handleOpenOasfModal,
    onTopologyApplied: handleTopologyApplied,
  })

  useEffect(() => {
    hasInitialViewportFitRef.current = false
    setTopologyApplied(false)
    setLayoutSyncGeneration(0)
    setLayoutSyncNodeIds([])
    setLayoutSyncFitViewport(false)
  }, [selectedWorkflowSummary?.name, pattern])

  useEffect(() => {
    if (!agenticError) return
    logger.error("agentic-workflows/graph-session", { detail: agenticError })
  }, [agenticError])

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
      const recruiterId = prevNodes.find((n) => {
        const l1 = String(customNodeDataFromNode(n).label ?? "")
          .toLowerCase()
          .trim()
        return l1.includes("recruiter")
      })?.id
      return prevNodes.map((node) => {
        const nodeData = customNodeDataFromNode(node)
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
    setNodes,
    handleOpenIdentityModal,
    handleOpenOasfModal,
    activeModal,
    activeNodeId,
    handleShowBadgeDetails,
    handleShowPolicyDetails,
    fitViewWithViewport,
    chatHeight,
    isExpanded,
    animationLockRef: animationLock,
    handleCloseModals,
    setOasfModalOpen,
  })

  useNodeTransportInterfaces(pattern, nodes, setNodes)

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
    if (pattern === "group_messaging") return
    const waitForAnimationAndRun = async () => {
      while (animationLock.current) await delay(100)
      animationLock.current = true
      const animate = async (ids: string[], active: boolean): Promise<void> => {
        ids.forEach((id: string) => updateStyle(id, active))
        await delay(DELAY_DURATION)
      }
      const animateGraph = async (): Promise<void> => {
        const animationSequence = deriveAnimationSequenceFromGraph(
          nodesRef.current,
          edgesRef.current,
        )
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
  }, [buttonClicked, setButtonClicked, aiReplied, pattern, updateStyle])

  useEffect(() => {
    if (!onLiveGraphConfig) return
    const title = selectedWorkflowSummary
      ? `${selectedWorkflowSummary.name} — ${selectedWorkflowSummary.scenario}`
      : ""
    const animationSequence = deriveAnimationSequenceFromGraph(nodes, edges)
    onLiveGraphConfig(
      graphConfigFromNodes(title, nodes, edges, animationSequence),
    )
  }, [onLiveGraphConfig, selectedWorkflowSummary, nodes, edges])

  const highlightNode = useCallback(
    (graphElementId: string) => {
      if (!graphElementId) return
      updateStyle(graphElementId, HIGHLIGHT.ON)
      setTimeout(() => updateStyle(graphElementId, HIGHLIGHT.OFF), 1800)
    },
    [updateStyle],
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
    oasfModalOpen,
    setOasfModalOpen,
    oasfModalData,
    onPaneClick,
    onNodeDrag,
    topologyApplied,
    agenticMode,
    agenticError,
    layoutSyncGeneration,
    layoutSyncNodeIds,
    layoutSyncFitViewport,
    handleLayoutSyncReady,
  }
}
