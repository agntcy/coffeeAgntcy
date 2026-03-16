/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { useState, useCallback } from "react"
import type {
  ModalType,
  ModalState,
  ModalPosition,
  ModalNodeData,
} from "@/types/modal"
import type { CustomNodeData } from "@/components/MainArea/Graph/Elements/types"

export type { ModalType, ModalState, ModalNodeData } from "@/types/modal"

export interface ModalActions {
  handleOpenIdentityModal: (
    nodeData: CustomNodeData,
    position: ModalPosition,
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
  const [activeNodeData, setActiveNodeData] = useState<ModalNodeData>(null)
  const [modalPosition, setModalPosition] = useState<ModalPosition>({
    x: 0,
    y: 0,
  })

  const handleOpenIdentityModal = useCallback(
    (
      nodeData: CustomNodeData,
      position: ModalPosition,
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
