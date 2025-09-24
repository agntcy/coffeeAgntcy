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
  Node,
  Edge,
} from "@xyflow/react"
import "@xyflow/react/dist/style.css"
import "./ReactFlow.css"
import SlimNode from "./Graph/TransportNode"
import CustomEdge from "./Graph/CustomEdge"
import CustomNode from "./Graph/CustomNode"
import { graphConfig, updateA2ALabels } from "@/utils/graphConfigs"
import { useViewportAwareFitView } from "@/hooks/useViewportAwareFitView"

const proOptions = { hideAttribution: true }

const nodeTypes = {
  slimNode: SlimNode,
  customNode: CustomNode,
}

const edgeTypes = {
  custom: CustomEdge,
}

interface AnimationStep {
  ids: string[]
}

interface GraphConfig {
  nodes: Node[]
  edges: Edge[]
  animationSequence: AnimationStep[]
}

interface MainAreaProps {
  buttonClicked: boolean
  setButtonClicked: (clicked: boolean) => void
  aiReplied: boolean
  setAiReplied: (replied: boolean) => void
  chatHeight?: number
  isExpanded?: boolean
}

const DELAY_DURATION = 500
const HIGHLIGHT = {
  ON: true,
  OFF: false,
} as const

const MainArea: React.FC<MainAreaProps> = ({
  buttonClicked,
  setButtonClicked,
  aiReplied,
  setAiReplied,
  chatHeight = 0,
  isExpanded = false,
}) => {
  const config: GraphConfig = graphConfig
  const fitViewWithViewport = useViewportAwareFitView()

  const [nodesDraggable, setNodesDraggable] = useState(true)
  const [nodesConnectable, setNodesConnectable] = useState(true)

  const [nodes, setNodes, onNodesChange] = useNodesState(config.nodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(config.edges)
  const animationLock = useRef<boolean>(false)

  useEffect(() => {
    updateA2ALabels(setEdges)

    const newConfig: GraphConfig = graphConfig
    setNodes(newConfig.nodes)
    setEdges(newConfig.edges)

    setTimeout(() => {
      fitViewWithViewport({
        chatHeight,
        isExpanded,
      })
    }, 100)
  }, [setNodes, setEdges, fitViewWithViewport, chatHeight, isExpanded])

  useEffect(() => {
    // Trigger fitView whenever chat height or expansion state changes
    fitViewWithViewport({
      chatHeight,
      isExpanded,
    })
  }, [chatHeight, isExpanded, fitViewWithViewport])

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
  }, [nodesDraggable, nodesConnectable])

  const delay = (ms: number): Promise<void> =>
    new Promise((resolve) => setTimeout(resolve, ms))

  const updateStyle = useCallback(
    (id: string, active: boolean): void => {
      setNodes((objs: Node[]) =>
        objs.map((obj: Node) =>
          obj.id === id ? { ...obj, data: { ...obj.data, active } } : obj,
        ),
      )
      setEdges((objs: Edge[]) =>
        objs.map((obj: Edge) =>
          obj.id === id ? { ...obj, data: { ...obj.data, active } } : obj,
        ),
      )
    },
    [setNodes, setEdges],
  )

  useEffect(() => {
    if (!buttonClicked && !aiReplied) return

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
        if (!aiReplied) {
          const animationSequence: AnimationStep[] = config.animationSequence
          for (const step of animationSequence) {
            await animate(step.ids, HIGHLIGHT.ON)
            await animate(step.ids, HIGHLIGHT.OFF)
          }
        } else {
          setAiReplied(false)
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
    config.animationSequence,
    updateStyle,
  ])

  return (
    <div className="bg-primary-bg order-1 flex h-full w-full flex-none flex-grow flex-col items-start self-stretch p-0">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        proOptions={proOptions}
        defaultViewport={{ x: 0, y: 0, zoom: 0.6 }}
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
