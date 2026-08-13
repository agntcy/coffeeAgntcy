/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useMemo, useRef } from "react"
import { ReactFlow, ReactFlowProvider } from "@xyflow/react"
import "@xyflow/react/dist/style.css"
import "./ReactFlow.css"
import { ReactFlowThemeGlobalStyles } from "./ReactFlowThemeGlobalStyles"
import { Box } from "@open-ui-kit/core"
import { useTheme } from "@mui/material/styles"
import useMediaQuery from "@mui/material/useMediaQuery"
import { isLayoutWidthBelowSm } from "@/constants/layoutBreakpoints"
import { useGraphCanvasLayout } from "@/contexts/graphCanvasLayout"
import TransportNode from "./Graph/Elements/transportNode"
import CustomEdge from "./Graph/Elements/CustomEdge"
import BranchingEdge from "./Graph/Elements/BranchingEdge"
import CustomNode from "./Graph/Elements/CustomNode"
import CustomControls from "./Graph/Elements/CustomControls"
import CustomControlsBar from "./Graph/Elements/CustomControlsBar"
import { GraphTopologyLayoutSync } from "./Graph/GraphTopologyLayoutSync"
import GraphDocumentationButton from "./Graph/Elements/GraphDocumentationButton"
import { isPlaceholderWorkflow } from "@/components/Sidebar/sidebar.utils"
import { getWorkflowDocumentationGithubUrl } from "@/urls"
import GraphNodeDetailDialogs from "./GraphNodeDetailDialogs"
import OasfRecordDialog from "./Graph/Directory/OasfRecordDialog"
import {
  GRAPH_MAX_ZOOM,
  GRAPH_MIN_ZOOM,
  GRAPH_DEFAULT_VIEWPORT,
} from "@/config/graphViewDefaults"
import { getAppShellBackgroundColor } from "./mainAreaBackground"
import {
  GraphCanvasOverlayError,
  GraphCanvasOverlayShell,
} from "./GraphCanvasOverlay"
import { LoadingSpinner } from "@/components/loading/LoadingSpinner"
import { useGraphCanvasFitViewOnResize } from "@/hooks/graph"
import { useElementSize } from "@/hooks/layout"
import { useMainArea, type MainAreaProps } from "./useMainArea"

const proOptions = { hideAttribution: true }

const nodeTypes = {
  transportNode: TransportNode,
  customNode: CustomNode,
}

const edgeTypes = {
  custom: CustomEdge,
  branching: BranchingEdge,
}

const MainArea: React.FC<MainAreaProps> = (props) => {
  const theme = useTheme()
  const { graphCanvasWidth } = useGraphCanvasLayout()
  const isViewportBelowSm = useMediaQuery(theme.breakpoints.down("sm"))
  const useCompactGraphControls = useMemo(() => {
    if (graphCanvasWidth !== undefined && graphCanvasWidth > 0) {
      return isLayoutWidthBelowSm(graphCanvasWidth)
    }
    return isViewportBelowSm
  }, [graphCanvasWidth, isViewportBelowSm])

  const {
    selectedWorkflowSummary,
    workflowCatalogLoading,
    workflowCatalogError,
  } = props
  const {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    nodesDraggable,
    setNodesDraggable,
    nodesConnectable,
    setNodesConnectable,
    activeDialog,
    activeNodeData,
    handleCloseDialogs,
    oasfDialogOpen,
    setOasfDialogOpen,
    oasfDialogData,
    onPaneClick,
    onNodeDrag,
    topologyApplied,
    agenticMode,
    agenticError,
    layoutSyncGeneration,
    layoutSyncNodeIds,
    layoutSyncFitViewport,
    handleLayoutSyncReady,
    fitViewWithViewport,
  } = useMainArea(props)

  const graphCanvasRef = useRef<HTMLDivElement>(null)
  const graphCanvasSize = useElementSize(graphCanvasRef)
  useGraphCanvasFitViewOnResize(
    graphCanvasSize,
    fitViewWithViewport,
    topologyApplied,
  )

  const activeWorkflowSummary =
    selectedWorkflowSummary && !isPlaceholderWorkflow(selectedWorkflowSummary)
      ? selectedWorkflowSummary
      : undefined

  const chatApiTarget = activeWorkflowSummary?.chat_api_target ?? null

  const overlayError = agenticError ?? workflowCatalogError ?? null
  const showLoading =
    !overlayError &&
    !topologyApplied &&
    (Boolean(workflowCatalogLoading) || agenticMode)

  const documentationUrl = activeWorkflowSummary
    ? getWorkflowDocumentationGithubUrl(activeWorkflowSummary.name)
    : undefined
  const documentationLabel = activeWorkflowSummary?.name

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
        {overlayError || showLoading ? (
          <GraphCanvasOverlayShell
            pointerEvents={overlayError ? "auto" : "none"}
          >
            {overlayError ? (
              <GraphCanvasOverlayError message={overlayError} />
            ) : (
              <LoadingSpinner message="Loading workflow graph..." />
            )}
          </GraphCanvasOverlayShell>
        ) : null}

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
              onNodeDrag={onNodeDrag}
              onPaneClick={onPaneClick}
              proOptions={proOptions}
              defaultViewport={GRAPH_DEFAULT_VIEWPORT}
              minZoom={GRAPH_MIN_ZOOM}
              maxZoom={GRAPH_MAX_ZOOM}
              nodesDraggable={nodesDraggable}
              nodesConnectable={nodesConnectable}
              elementsSelectable={nodesDraggable}
              elevateNodesOnSelect={false}
              style={{ width: "100%", height: "100%" }}
            >
              <GraphTopologyLayoutSync
                generation={layoutSyncGeneration}
                nodeIds={layoutSyncNodeIds}
                fitViewport={layoutSyncFitViewport}
                onReady={handleLayoutSyncReady}
              />
              {!useCompactGraphControls ? (
                <CustomControls
                  isInteractive={graphInteractivityEnabled}
                  onToggleInteractivity={handleToggleGraphInteractivity}
                />
              ) : null}
              <GraphDocumentationButton
                documentationUrl={documentationUrl}
                documentationLabel={documentationLabel}
              />
            </ReactFlow>
          </Box>
          {useCompactGraphControls ? (
            <CustomControlsBar
              isInteractive={graphInteractivityEnabled}
              onToggleInteractivity={handleToggleGraphInteractivity}
            />
          ) : null}
        </Box>

        <GraphNodeDetailDialogs
          activeDialog={activeDialog}
          activeNodeData={activeNodeData}
          onClose={handleCloseDialogs}
        />

        <OasfRecordDialog
          isOpen={oasfDialogOpen}
          onClose={() => setOasfDialogOpen(false)}
          nodeName={oasfDialogData?.label || ""}
          nodeData={oasfDialogData}
          chatApiTarget={chatApiTarget}
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
