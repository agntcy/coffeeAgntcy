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
import { PatternType } from "@/App"
import TransportNode from "./Graph/transportNode"
import CustomEdge from "./Graph/CustomEdge"
import BranchingEdge from "./Graph/BranchingEdge"
import CustomNode from "./Graph/CustomNode"
import {
  getGraphConfig,
  updateTransportLabels,
  GraphConfig,
} from "@/utils/graphConfigs"
import { useViewportAwareFitView } from "@/hooks/useViewportAwareFitView"

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
}) => {
  const fitViewWithViewport = useViewportAwareFitView()

  const isGroupCommConnected =
    pattern !== "group_communication" || groupCommResponseReceived

  const config: GraphConfig = getGraphConfig(pattern, isGroupCommConnected)

  const [nodesDraggable, setNodesDraggable] = useState(true)
  const [nodesConnectable, setNodesConnectable] = useState(true)

  const [nodes, setNodes, onNodesChange] = useNodesState(config.nodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(config.edges)
  const animationLock = useRef<boolean>(false)

  useEffect(() => {
    const updateGraph = async () => {
      const newConfig = getGraphConfig(pattern, isGroupCommConnected)

      setNodes(newConfig.nodes)

      await new Promise((resolve) => setTimeout(resolve, 50))

      setEdges(newConfig.edges)

      await updateTransportLabels(setNodes, setEdges, pattern)

      setTimeout(() => {
        fitViewWithViewport({
          chatHeight: 0,
          isExpanded: false,
        })
      }, 200)
    }

    updateGraph()
  }, [fitViewWithViewport, pattern, isGroupCommConnected, setNodes, setEdges])

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
    config.animationSequence,
    updateStyle,
    setNodes,
    setEdges,
  ])

  const onNodeDrag = useCallback(() => {}, [])

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
    </div>
  )
}

const MainAreaWithProvider: React.FC<MainAreaProps> = (props) => (
  <ReactFlowProvider>
    <MainArea {...props} />
  </ReactFlowProvider>
)

export default MainAreaWithProvider
