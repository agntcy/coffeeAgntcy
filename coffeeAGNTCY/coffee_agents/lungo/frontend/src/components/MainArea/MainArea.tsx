/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { ReactFlow, ReactFlowProvider } from "@xyflow/react"
import "@xyflow/react/dist/style.css"
import "./ReactFlow.css"
import { ReactFlowThemeGlobalStyles } from "./ReactFlowThemeGlobalStyles"
import { Box } from "@open-ui-kit/core"
import TransportNode from "./Graph/Elements/transportNode"
import CustomEdge from "./Graph/Elements/CustomEdge"
import BranchingEdge from "./Graph/Elements/BranchingEdge"
import CustomNode from "./Graph/Elements/CustomNode"
import CustomControls from "./Graph/Elements/CustomControls"
import GraphDocumentationButton from "./Graph/Elements/GraphDocumentationButton"
import { isPlaceholderWorkflow } from "@/components/Sidebar/sidebar.utils"
import { getWorkflowDocumentationGithubUrl } from "@/urls"
import ModalContainer from "./ModalContainer"
import OasfRecordModal from "./Graph/Directory/OasfRecordModal"
import {
  GRAPH_MAX_ZOOM,
  GRAPH_MIN_ZOOM,
  GRAPH_DEFAULT_VIEWPORT,
} from "@/config/graphViewDefaults"
import { getAppShellBackgroundColor } from "./mainAreaBackground"
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
  const { selectedWorkflowSummary } = props
  const {
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
  } = useMainArea(props)

  const activeWorkflowSummary =
    selectedWorkflowSummary && !isPlaceholderWorkflow(selectedWorkflowSummary)
      ? selectedWorkflowSummary
      : undefined

  const documentationUrl = activeWorkflowSummary
    ? getWorkflowDocumentationGithubUrl(activeWorkflowSummary.name)
    : undefined
  const documentationLabel = activeWorkflowSummary?.name

  return (
    <>
      <ReactFlowThemeGlobalStyles />
      <Box
        sx={{
          order: 1,
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
        >
          <CustomControls
            isInteractive={nodesDraggable && nodesConnectable}
            onToggleInteractivity={() => {
              const next = !(nodesDraggable && nodesConnectable)
              setNodesDraggable(next)
              setNodesConnectable(next)
            }}
          />
          <GraphDocumentationButton
            documentationUrl={documentationUrl}
            documentationLabel={documentationLabel}
          />
        </ReactFlow>

        <ModalContainer
          activeModal={activeModal}
          activeNodeData={activeNodeData}
          onClose={handleCloseModals}
        />

        <OasfRecordModal
          isOpen={oasfModalOpen}
          onClose={() => setOasfModalOpen(false)}
          nodeName={oasfModalData?.label1 || ""}
          nodeData={oasfModalData}
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
