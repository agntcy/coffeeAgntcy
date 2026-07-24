/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useEffect } from "react"
import type { Node } from "@xyflow/react"
import type { ModalType } from "@/types/modal"
import type { CustomNodeData } from "./Graph/Elements/types"

function withNodeModalHandlers(
  node: Node,
  {
    activeModal,
    activeNodeId,
    handleOpenIdentityModal,
    handleOpenOasfModal,
    handleCloseModals,
    handleShowBadgeDetails,
    handleShowPolicyDetails,
  }: {
    activeModal: ModalType
    activeNodeId: string | null
    handleOpenIdentityModal: (nodeId: string, nodeData: CustomNodeData) => void
    handleOpenOasfModal: (nodeData: CustomNodeData) => void
    handleCloseModals: () => void
    handleShowBadgeDetails: () => void
    handleShowPolicyDetails: () => void
  },
): Record<string, unknown> {
  return {
    ...node.data,
    onOpenIdentityModal: handleOpenIdentityModal,
    onOpenOasfModal: handleOpenOasfModal,
    isIdentityDropdownOpen:
      activeModal === "identity" && activeNodeId === node.id,
    onCloseIdentityDropdown: handleCloseModals,
    onShowBadgeDetails: handleShowBadgeDetails,
    onShowPolicyDetails: handleShowPolicyDetails,
    isModalOpen: Boolean(activeModal && activeNodeId === node.id),
  }
}

export interface UseMainAreaGraphEffectsParams {
  pattern: string
  setNodes: React.Dispatch<React.SetStateAction<Node[]>>
  handleOpenIdentityModal: (nodeId: string, nodeData: CustomNodeData) => void
  handleOpenOasfModal: (nodeData: CustomNodeData) => void
  activeModal: ModalType
  activeNodeId: string | null
  handleShowBadgeDetails: () => void
  handleShowPolicyDetails: () => void
  fitViewWithViewport: (opts: {
    chatHeight: number
    isExpanded: boolean
  }) => void
  chatHeight: number
  isExpanded: boolean
  animationLockRef: React.MutableRefObject<boolean>
  handleCloseModals: () => void
  setOasfModalOpen: (open: boolean) => void
}

/** Runs effects that inject modal handlers onto live nodes and fit the viewport. */
export function useMainAreaGraphEffects({
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
  animationLockRef,
  handleCloseModals,
  setOasfModalOpen,
}: UseMainAreaGraphEffectsParams) {
  useEffect(() => {
    animationLockRef.current = false
  }, [pattern, animationLockRef])

  useEffect(() => {
    handleCloseModals()
    setOasfModalOpen(false)
  }, [pattern, handleCloseModals, setOasfModalOpen])

  useEffect(() => {
    setNodes((nodes) =>
      nodes.map((node) => ({
        ...node,
        data: withNodeModalHandlers(node, {
          activeModal,
          activeNodeId,
          handleOpenIdentityModal,
          handleOpenOasfModal,
          handleCloseModals,
          handleShowBadgeDetails,
          handleShowPolicyDetails,
        }),
      })),
    )
  }, [
    handleOpenIdentityModal,
    handleOpenOasfModal,
    handleCloseModals,
    handleShowBadgeDetails,
    handleShowPolicyDetails,
    activeModal,
    activeNodeId,
    setNodes,
  ])

  useEffect(() => {
    fitViewWithViewport({ chatHeight, isExpanded })
  }, [chatHeight, isExpanded, fitViewWithViewport])
}
