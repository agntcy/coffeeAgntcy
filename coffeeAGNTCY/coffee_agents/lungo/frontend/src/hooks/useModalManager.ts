/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useState, useCallback } from "react"

export type ModalType = "identity" | "badge" | "policy" | null

export interface ModalState {
  activeModal: ModalType
  activeNodeData: any
  modalPosition: { x: number; y: number }
}

export interface ModalActions {
  handleOpenIdentityModal: (
    nodeData: any,
    position: { x: number; y: number },
    nodeName?: string,
    data?: any,
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
  const [activeNodeData, setActiveNodeData] = useState<any>(null)
  const [modalPosition, setModalPosition] = useState({ x: 0, y: 0 })

  const handleOpenIdentityModal = useCallback(
    (
      nodeData: any,
      position: { x: number; y: number },
      _nodeName?: string,
      _data?: any,
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
