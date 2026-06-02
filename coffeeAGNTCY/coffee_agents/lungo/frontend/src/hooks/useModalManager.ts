/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useState, useCallback } from "react"
import type { ModalType, ModalState, ModalNodeData } from "@/types/modal"
import type { CustomNodeData } from "@/components/MainArea/Graph/Elements/types"

export type { ModalType, ModalState, ModalNodeData } from "@/types/modal"

export interface ModalActions {
  handleOpenIdentityModal: (nodeId: string, nodeData: CustomNodeData) => void
  handleCloseModals: () => void
  handleShowBadgeDetails: () => void
  handleShowPolicyDetails: () => void
  handlePaneClick: () => void
}

export interface UseModalManagerReturn extends ModalState, ModalActions {
  activeNodeId: string | null
}

export const useModalManager = (): UseModalManagerReturn => {
  const [activeModal, setActiveModal] = useState<ModalType>(null)
  const [activeNodeId, setActiveNodeId] = useState<string | null>(null)
  const [activeNodeData, setActiveNodeData] = useState<ModalNodeData>(null)

  const handleOpenIdentityModal = useCallback(
    (nodeId: string, nodeData: CustomNodeData) => {
      setActiveNodeId(nodeId)
      setActiveNodeData({ ...nodeData })
      setActiveModal("identity")
    },
    [],
  )

  const handleCloseModals = useCallback(() => {
    setActiveModal(null)
    setActiveNodeId(null)
    setActiveNodeData(null)
  }, [])

  const handleShowBadgeDetails = useCallback(() => {
    setActiveModal("badge")
  }, [])

  const handleShowPolicyDetails = useCallback(() => {
    setActiveModal("policy")
  }, [])

  const handlePaneClick = useCallback(() => {
    if (activeModal) {
      handleCloseModals()
    }
  }, [activeModal, handleCloseModals])

  return {
    activeModal,
    activeNodeId,
    activeNodeData,
    handleOpenIdentityModal,
    handleCloseModals,
    handleShowBadgeDetails,
    handleShowPolicyDetails,
    handlePaneClick,
  }
}
