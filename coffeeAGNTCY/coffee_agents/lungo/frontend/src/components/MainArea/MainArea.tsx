/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { ReactFlow, ReactFlowProvider, Controls } from "@xyflow/react"
import "@xyflow/react/dist/style.css"
import "./ReactFlow.css"
import TransportNode from "./Graph/Elements/transportNode"
import CustomEdge from "./Graph/Elements/CustomEdge"
import BranchingEdge from "./Graph/Elements/BranchingEdge"
import CustomNode from "./Graph/Elements/CustomNode"
import ModalContainer from "./ModalContainer"
import OasfRecordModal from "./Graph/Directory/OasfRecordModal"
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
  } = useMainArea(props)

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

      <OasfRecordModal
        isOpen={oasfModalOpen}
        onClose={() => setOasfModalOpen(false)}
        nodeName={oasfModalData?.label1 || ""}
        nodeData={oasfModalData}
        position={oasfModalPosition}
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
