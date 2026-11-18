/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useEffect, useRef, useCallback, useState, useMemo } from "react"
import {
  ReactFlow,
  ReactFlowProvider,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
} from "@xyflow/react"
import "@xyflow/react/dist/style.css"
import "./ReactFlow.css"
import { Box } from "@open-ui-kit/core"
import { isLayoutWidthBelowSm } from "@/constants/layoutBreakpoints"
import { useGraphCanvasLayout } from "@/contexts/graphCanvasLayout"
import { ReactFlowThemeGlobalStyles } from "./ReactFlowThemeGlobalStyles"
import { getAppShellBackgroundColor } from "./mainAreaBackground"
import SlimNode from "./Graph/TransportNode"
import CustomEdge from "./Graph/CustomEdge"
import CustomNode from "./Graph/CustomNode"
import CustomControls from "./Graph/Elements/controls/CustomControls"
import CustomControlsBar from "./Graph/Elements/controls/CustomControlsBar"
import OasfRecordModal from "./Graph/Directory/OasfRecordModal"
import { graphConfig, updateA2ALabels } from "@/utils/graphConfigs"
import {
  GRAPH_DEFAULT_VIEWPORT,
  GRAPH_MAX_ZOOM,
  GRAPH_MIN_ZOOM,
} from "@/config/graphViewDefaults"
import { useViewportAwareFitView } from "@/hooks/useViewportAwareFitView"
import { useGraphCanvasFitViewOnResize } from "@/hooks/graph/useGraphCanvasFitViewOnResize"
import {
  useElementHeight,
  useIsBelowSmBreakpoint,
  type ElementSize,
} from "@/hooks/layout"
import type { CustomNodeData } from "./Graph/CustomNode"

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
}) => {
  const { graphCanvasWidth } = useGraphCanvasLayout()
  const isViewportBelowSm = useIsBelowSmBreakpoint()
  const useCompactGraphControls = useMemo(() => {
    if (graphCanvasWidth !== undefined && graphCanvasWidth > 0) {
      return isLayoutWidthBelowSm(graphCanvasWidth)
    }
    return isViewportBelowSm
  }, [graphCanvasWidth, isViewportBelowSm])

  const config: GraphConfig = graphConfig
  const fitViewWithViewport = useViewportAwareFitView()

  const [nodesDraggable, setNodesDraggable] = useState(true)
  const [nodesConnectable, setNodesConnectable] = useState(true)

  const [nodes, setNodes, onNodesChange] = useNodesState(config.nodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(config.edges)
  const animationLock = useRef<boolean>(false)

  const [oasfModalOpen, setOasfModalOpen] = useState(false)
  const [oasfModalData, setOasfModalData] = useState<CustomNodeData | null>(
    null,
  )

  const graphCanvasRef = useRef<HTMLDivElement>(null)
  const graphCanvasHeight = useElementHeight(graphCanvasRef)
  const graphCanvasSize = useMemo((): ElementSize | undefined => {
    if (
      graphCanvasWidth === undefined ||
      graphCanvasWidth <= 0 ||
      graphCanvasHeight === undefined ||
      graphCanvasHeight <= 0
    ) {
      return undefined
    }
    return { width: graphCanvasWidth, height: graphCanvasHeight }
  }, [graphCanvasWidth, graphCanvasHeight])

  const triggerFitView = useCallback(() => {
    fitViewWithViewport()
  }, [fitViewWithViewport])

  useGraphCanvasFitViewOnResize(graphCanvasSize, triggerFitView, true)

  const handleOpenOasfModal = useCallback((nodeData: CustomNodeData) => {
    setOasfModalData(nodeData)
    setOasfModalOpen(true)
  }, [])

  const handleCloseOasfModal = useCallback(() => {
    setOasfModalOpen(false)
    setOasfModalData(null)
  }, [])

  useEffect(() => {
    updateA2ALabels(setEdges)

    const newConfig: GraphConfig = graphConfig
    const nodesWithHandlers = newConfig.nodes.map((node) => ({
      ...node,
      data: {
        ...node.data,
        onOpenOasfModal: handleOpenOasfModal,
      },
    }))
    setNodes(nodesWithHandlers)
    setEdges(newConfig.edges)

    const frameId = window.requestAnimationFrame(() => {
      fitViewWithViewport()
    })
    return () => {
      window.cancelAnimationFrame(frameId)
    }
  }, [setNodes, setEdges, fitViewWithViewport, handleOpenOasfModal])

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

  const graphInteractivityEnabled = nodesDraggable && nodesConnectable
  const handleToggleGraphInteractivity = () => {
    const next = !graphInteractivityEnabled
    setNodesDraggable(next)
    setNodesConnectable(next)
  }

  return (
    <>
      <ReactFlowThemeGlobalStyles />
      <Box
        sx={{
          order: 1,
          position: "relative",
          display: "flex",
          width: "100%",
          height: "100%",
          flexShrink: 0,
          flexGrow: 1,
          flexDirection: "column",
          alignItems: "flex-start",
          alignSelf: "stretch",
          p: 0,
          bgcolor: (theme) => getAppShellBackgroundColor(theme),
        }}
      >
        <Box
          sx={{
            position: "relative",
            display: "grid",
            flex: 1,
            alignSelf: "stretch",
            width: "100%",
            minHeight: 0,
            minWidth: 0,
            overflow: "hidden",
            gridTemplateRows: useCompactGraphControls
              ? "minmax(0, 1fr) auto"
              : "minmax(0, 1fr)",
          }}
        >
          <Box
            ref={graphCanvasRef}
            sx={{
              position: "relative",
              minHeight: 0,
              minWidth: 0,
              width: "100%",
              height: "100%",
            }}
          >
            <ReactFlow
              nodes={nodes}
              edges={edges}
              nodeTypes={nodeTypes}
              edgeTypes={edgeTypes}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              proOptions={proOptions}
              defaultViewport={GRAPH_DEFAULT_VIEWPORT}
              minZoom={GRAPH_MIN_ZOOM}
              maxZoom={GRAPH_MAX_ZOOM}
              nodesDraggable={nodesDraggable}
              nodesConnectable={nodesConnectable}
              elementsSelectable={nodesDraggable}
              style={{ width: "100%", height: "100%" }}
            >
              {!useCompactGraphControls ? (
                <CustomControls
                  isInteractive={graphInteractivityEnabled}
                  onToggleInteractivity={handleToggleGraphInteractivity}
                />
              ) : null}
            </ReactFlow>
          </Box>
          {useCompactGraphControls ? (
            <CustomControlsBar
              isInteractive={graphInteractivityEnabled}
              onToggleInteractivity={handleToggleGraphInteractivity}
            />
          ) : null}
        </Box>

        <OasfRecordModal
          isOpen={oasfModalOpen}
          onClose={handleCloseOasfModal}
          nodeName={oasfModalData?.label1 ?? ""}
          nodeData={oasfModalData ?? null}
        />
      </Box>
    </>
  )
}

const MainAreaWithProvider: React.FC<MainAreaProps> = (props) => (
  <ReactFlowProvider>
    <MainArea {...props} />
  </ReactFlowProvider>
)

export default MainAreaWithProvider
