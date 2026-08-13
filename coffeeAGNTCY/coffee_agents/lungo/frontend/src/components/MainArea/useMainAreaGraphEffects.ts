/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useEffect } from "react"
import type { Node } from "@xyflow/react"
import type { DialogType } from "@/types/dialog"
import type { CustomNodeData } from "./Graph/Elements/types"

function withNodeDialogHandlers(
  node: Node,
  {
    activeDialog,
    activeNodeId,
    handleOpenIdentityDialog,
    handleOpenOasfDialog,
    handleCloseDialogs,
    handleShowBadgeDetails,
    handleShowPolicyDetails,
  }: {
    activeDialog: DialogType
    activeNodeId: string | null
    handleOpenIdentityDialog: (nodeId: string, nodeData: CustomNodeData) => void
    handleOpenOasfDialog: (nodeData: CustomNodeData) => void
    handleCloseDialogs: () => void
    handleShowBadgeDetails: () => void
    handleShowPolicyDetails: () => void
  },
): Record<string, unknown> {
  return {
    ...node.data,
    onOpenIdentityDialog: handleOpenIdentityDialog,
    onOpenOasfDialog: handleOpenOasfDialog,
    isIdentityDropdownOpen:
      activeDialog === "identity" && activeNodeId === node.id,
    onCloseIdentityDropdown: handleCloseDialogs,
    onShowBadgeDetails: handleShowBadgeDetails,
    onShowPolicyDetails: handleShowPolicyDetails,
    isDialogOpen: Boolean(activeDialog && activeNodeId === node.id),
  }
}

export interface UseMainAreaGraphEffectsParams {
  pattern: string
  setNodes: React.Dispatch<React.SetStateAction<Node[]>>
  handleOpenIdentityDialog: (nodeId: string, nodeData: CustomNodeData) => void
  handleOpenOasfDialog: (nodeData: CustomNodeData) => void
  activeDialog: DialogType
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
  handleCloseDialogs: () => void
  setOasfDialogOpen: (open: boolean) => void
}

/** Runs effects that inject dialog handlers onto live nodes and fit the viewport. */
export function useMainAreaGraphEffects({
  pattern,
  setNodes,
  handleOpenIdentityDialog,
  handleOpenOasfDialog,
  activeDialog,
  activeNodeId,
  handleShowBadgeDetails,
  handleShowPolicyDetails,
  fitViewWithViewport,
  chatHeight,
  isExpanded,
  animationLockRef,
  handleCloseDialogs,
  setOasfDialogOpen,
}: UseMainAreaGraphEffectsParams) {
  useEffect(() => {
    animationLockRef.current = false
  }, [pattern, animationLockRef])

  useEffect(() => {
    handleCloseDialogs()
    setOasfDialogOpen(false)
  }, [pattern, handleCloseDialogs, setOasfDialogOpen])

  useEffect(() => {
    setNodes((nodes) =>
      nodes.map((node) => ({
        ...node,
        data: withNodeDialogHandlers(node, {
          activeDialog,
          activeNodeId,
          handleOpenIdentityDialog,
          handleOpenOasfDialog,
          handleCloseDialogs,
          handleShowBadgeDetails,
          handleShowPolicyDetails,
        }),
      })),
    )
  }, [
    handleOpenIdentityDialog,
    handleOpenOasfDialog,
    handleCloseDialogs,
    handleShowBadgeDetails,
    handleShowPolicyDetails,
    activeDialog,
    activeNodeId,
    setNodes,
  ])

  useEffect(() => {
    fitViewWithViewport({ chatHeight, isExpanded })
  }, [chatHeight, isExpanded, fitViewWithViewport])
}
