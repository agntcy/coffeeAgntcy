/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useEffect, useRef, useCallback } from "react"
import {
  ReactFlow,
  ReactFlowProvider,
  useNodesState,
  useEdgesState,
  useReactFlow,
  Controls,
} from "@xyflow/react"
import "@xyflow/react/dist/style.css"
import "./ReactFlow.css"
import { PatternType } from "@/App"
import TransportNode from "./Graph/SlimNode"
import CustomEdge from "./Graph/CustomEdge"
import CustomNode from "./Graph/CustomNode"
import {
  getGraphConfig,
  updateTransportLabels,
  GraphConfig,
} from "@/utils/graphConfigs"

const proOptions = { hideAttribution: true }

const nodeTypes = {
  transportNode: TransportNode,
  customNode: CustomNode,
}

const edgeTypes = {
  custom: CustomEdge,
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
}) => {
  const { fitView } = useReactFlow()

  const config: GraphConfig = getGraphConfig(pattern)
  const [nodes, setNodes, onNodesChange] = useNodesState(config.nodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(config.edges)
  const animationLock = useRef<boolean>(false)

  useEffect(() => {
    updateTransportLabels(setNodes, setEdges)

    const newConfig = getGraphConfig(pattern)
    setNodes(newConfig.nodes)
    setEdges(newConfig.edges)

    setTimeout(() => {
      fitView({
        padding: 0.45,
        duration: 300,
        minZoom: 0.5,
        maxZoom: 1.1,
      })
    }, 100)
  }, [pattern, setNodes, setEdges, fitView])

  const delay = (ms: number): Promise<void> =>
    new Promise((resolve) => setTimeout(resolve, ms))

  const updateStyle = useCallback(
    (id: string, active: boolean): void => {
      setNodes((objs) =>
        objs.map((obj) =>
          obj.id === id ? { ...obj, data: { ...obj.data, active } } : obj,
        ),
      )
      setEdges((objs) =>
        objs.map((obj) =>
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
        defaultViewport={{ x: 0, y: 0, zoom: 0.75 }}
        minZoom={0.15}
        maxZoom={1.8}
      >
        <Controls />
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
