/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useState, useCallback } from "react"
import type { DialogType, DialogState, DialogNodeData } from "@/types/dialog"
import type { CustomNodeData } from "@/components/MainArea/Graph/Elements/types"

export type { DialogType, DialogState, DialogNodeData } from "@/types/dialog"

export interface DialogActions {
  handleOpenIdentityDialog: (nodeId: string, nodeData: CustomNodeData) => void
  handleCloseDialogs: () => void
  handleShowBadgeDetails: () => void
  handleShowPolicyDetails: () => void
  handlePaneClick: () => void
}

export interface UseDialogManagerReturn extends DialogState, DialogActions {
  activeNodeId: string | null
}

export const useDialogManager = (): UseDialogManagerReturn => {
  const [activeDialog, setActiveDialog] = useState<DialogType>(null)
  const [activeNodeId, setActiveNodeId] = useState<string | null>(null)
  const [activeNodeData, setActiveNodeData] = useState<DialogNodeData>(null)

  const handleOpenIdentityDialog = useCallback(
    (nodeId: string, nodeData: CustomNodeData) => {
      setActiveNodeId(nodeId)
      setActiveNodeData({ ...nodeData })
      setActiveDialog("identity")
    },
    [],
  )

  const handleCloseDialogs = useCallback(() => {
    setActiveDialog(null)
    setActiveNodeId(null)
    setActiveNodeData(null)
  }, [])

  const handleShowBadgeDetails = useCallback(() => {
    setActiveDialog("badge")
  }, [])

  const handleShowPolicyDetails = useCallback(() => {
    setActiveDialog("policy")
  }, [])

  const handlePaneClick = useCallback(() => {
    if (activeDialog) {
      handleCloseDialogs()
    }
  }, [activeDialog, handleCloseDialogs])

  return {
    activeDialog,
    activeNodeId,
    activeNodeData,
    handleOpenIdentityDialog,
    handleCloseDialogs,
    handleShowBadgeDetails,
    handleShowPolicyDetails,
    handlePaneClick,
  }
}
