/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { CustomNodeData } from "@/components/MainArea/Graph/Elements/types"
import { useState, useCallback } from "react"

export type ModalType = "identity" | "badge" | "policy" | null

/** Node data held in modal state; may include modal-only fields like isMcpServer. */
export type ModalNodeData = CustomNodeData & { isMcpServer?: boolean }

export interface ModalState {
  activeModal: ModalType
  activeNodeData: ModalNodeData | null
  modalPosition: { x: number; y: number }
}

export interface ModalActions {
  handleOpenIdentityModal: (
    nodeData: CustomNodeData,
    position: { x: number; y: number },
    nodeName?: string,
    data?: CustomNodeData,
    isMcpServer?: boolean,
  ) => void
  handleCloseModals: () => void
  handleShowBadgeDetails: () => void
  handleShowPolicyDetails: () => void
  handlePaneClick: () => void
}

export interface UseModalManagerReturn extends ModalState, ModalActions {}

export const useModalManager = (): UseModalManagerReturn => {
  const [activeModal, setActiveModal] = useState<ModalType>(null)
  const [activeNodeData, setActiveNodeData] = useState<ModalNodeData | null>(
    null,
  )
  const [modalPosition, setModalPosition] = useState({ x: 0, y: 0 })

  const handleOpenIdentityModal = useCallback(
    (
      nodeData: CustomNodeData,
      position: { x: number; y: number },
      _nodeName?: string,
      _data?: CustomNodeData,
      isMcpServer?: boolean,
    ) => {
      setActiveNodeData({ ...nodeData, isMcpServer })
      setModalPosition(position)
      setActiveModal("identity")
    },
    [],
  )

  const handleCloseModals = useCallback(() => {
    setActiveModal(null)
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
    activeNodeData,
    modalPosition,

    handleOpenIdentityModal,
    handleCloseModals,
    handleShowBadgeDetails,
    handleShowPolicyDetails,
    handlePaneClick,
  }
}
