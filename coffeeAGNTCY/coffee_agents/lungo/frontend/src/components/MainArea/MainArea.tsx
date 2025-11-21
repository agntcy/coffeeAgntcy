/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useEffect, useRef, useCallback, useState } from "react"
import {
  ReactFlow,
  ReactFlowProvider,
  useNodesState,
  useEdgesState,
  Controls,
} from "@xyflow/react"
import "@xyflow/react/dist/style.css"
import "./ReactFlow.css"
import { PatternType } from "@/utils/patternUtils"
import TransportNode from "./Graph/Elements/transportNode"
import CustomEdge from "./Graph/Elements/CustomEdge"
import BranchingEdge from "./Graph/Elements/BranchingEdge"
import CustomNode from "./Graph/Elements/CustomNode"
import ModalContainer from "./ModalContainer"
import {
  getGraphConfig,
  updateTransportLabels,
  GraphConfig,
} from "@/utils/graphConfigs"
import {
  isStreamingPattern,
  supportsTransportUpdates,
} from "@/utils/patternUtils"
import { useViewportAwareFitView } from "@/hooks/useViewportAwareFitView"
import { useModalManager } from "@/hooks/useModalManager"

const proOptions = { hideAttribution: true }

const nodeTypes = {
  transportNode: TransportNode,
  customNode: CustomNode,
}

const edgeTypes = {
  custom: CustomEdge,
  branching: BranchingEdge,
}

interface AnimationStep {
  ids: string[]
}

interface MainAreaProps {
  pattern: PatternType
  buttonClicked: boolean
  setButtonClicked: (clicked: boolean) => void
  aiReplied: boolean
  setAiReplied: (replied: boolean) => void
  chatHeight?: number
  isExpanded?: boolean
  groupCommResponseReceived?: boolean
  onNodeHighlight?: (highlightFunction: (nodeId: string) => void) => void
}

const DELAY_DURATION = 500
const HIGHLIGHT = {
  ON: true,
  OFF: false,
} as const

const MainArea: React.FC<MainAreaProps> = ({
  pattern,
  buttonClicked,
  setButtonClicked,
  aiReplied,
  setAiReplied,
  chatHeight = 0,
  isExpanded = false,
  groupCommResponseReceived = false,
  onNodeHighlight,
}) => {
  const fitViewWithViewport = useViewportAwareFitView()

  const isGroupCommConnected =
    pattern !== "group_communication" || groupCommResponseReceived

  const config: GraphConfig = getGraphConfig(pattern, isGroupCommConnected)

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

  useEffect(() => {
    animationLock.current = false
  }, [pattern])

  useEffect(() => {
    handleCloseModals()
  }, [pattern, handleCloseModals])

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
      const newConfig = getGraphConfig(pattern, isGroupCommConnected)

      const nodesWithHandlers = newConfig.nodes.map((node) => ({
        ...node,
        data: {
          ...node.data,
          onOpenIdentityModal: handleOpenIdentityModal,
          isModalOpen: !!(activeModal && activeNodeData?.id === node.id),
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
        fitViewWithViewport({
          chatHeight: 0,
          isExpanded: false,
        })
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

    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange)
    }
  }, [pattern, setNodes, setEdges])

  useEffect(() => {
    fitViewWithViewport({
      chatHeight,
      isExpanded,
    })
  }, [chatHeight, isExpanded, fitViewWithViewport])

  useEffect(() => {
    const checkEdges = () => {
      const expectedEdges = config.edges.length
      const renderedEdges =
        document.querySelectorAll(".react-flow__edge").length

      if (expectedEdges > 0 && renderedEdges === 0 && !animationLock.current) {
        setEdges([])
        setTimeout(() => {
          setEdges(config.edges)
        }, 100)
      }
    }

    const intervalId = setInterval(checkEdges, 2000)

    const timeoutId = setTimeout(checkEdges, 1000)

    return () => {
      clearInterval(intervalId)
      clearTimeout(timeoutId)
    }
  }, [config.edges, setEdges])

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
      while (animationLock.current) {
        await delay(100)
      }

      animationLock.current = true

      const animate = async (ids: string[], active: boolean): Promise<void> => {
        ids.forEach((id: string) => updateStyle(id, active))
        await delay(DELAY_DURATION)
      }

      const animateGraph = async (): Promise<void> => {
        const animationSequence: AnimationStep[] = config.animationSequence
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
    setNodes,
    setEdges,
  ])

  const highlightNode = useCallback(
    (nodeId: string) => {
      if (!nodeId) return

      if (pattern === "group_communication") {
        updateStyle(nodeId, HIGHLIGHT.ON)

        setTimeout(() => {
          updateStyle(nodeId, HIGHLIGHT.OFF)
        }, 1800)
      }
    },
    [updateStyle, pattern],
  )

  useEffect(() => {
    if (onNodeHighlight) {
      onNodeHighlight(highlightNode)
    }
  }, [onNodeHighlight, highlightNode])

  const onNodeDrag = useCallback(() => {}, [])

  const onPaneClick = modalPaneClick

  return (
    <div className="bg-primary-bg order-1 flex h-full w-full flex-none flex-grow flex-col items-start self-stretch p-0">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeDrag={onNodeDrag}
        onPaneClick={onPaneClick}
        proOptions={proOptions}
        defaultViewport={{ x: 0, y: 0, zoom: 0.75 }}
        minZoom={0.15}
        maxZoom={1.8}
        nodesDraggable={nodesDraggable}
        nodesConnectable={nodesConnectable}
        elementsSelectable={nodesDraggable}
      >
        <Controls
          onInteractiveChange={(interactiveEnabled) => {
            setNodesDraggable(interactiveEnabled)
            setNodesConnectable(interactiveEnabled)
          }}
        />
      </ReactFlow>

      <ModalContainer
        activeModal={activeModal}
        activeNodeData={activeNodeData}
        modalPosition={modalPosition}
        onClose={handleCloseModals}
        onShowBadgeDetails={handleShowBadgeDetails}
        onShowPolicyDetails={handleShowPolicyDetails}
      />
    </div>
  )
}

const MainAreaWithProvider: React.FC<MainAreaProps> = (props) => (
  <ReactFlowProvider>
    <MainArea {...props} />
  </ReactFlowProvider>
)

export default MainAreaWithProvider
