/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import IdentityModal from "./Graph/Identity/IdentityModal"
import BadgeDetailsModal from "./Graph/Identity/BadgeDetailsModal"
import PolicyDetailsModal from "./Graph/Identity/PolicyDetailsModal"
import { ModalType } from "@/hooks/useModalManager"

interface ModalContainerProps {
  activeModal: ModalType
  activeNodeData: any
  modalPosition: { x: number; y: number }
  onClose: () => void
  onShowBadgeDetails: () => void
  onShowPolicyDetails: () => void
}

const ModalContainer: React.FC<ModalContainerProps> = ({
  activeModal,
  activeNodeData,
  modalPosition,
  onClose,
  onShowBadgeDetails,
  onShowPolicyDetails,
}) => {
  const farmName = activeNodeData?.farmName || activeNodeData?.label1 || ""

  return (
    <>
      <IdentityModal
        isOpen={activeModal === "identity"}
        onClose={onClose}
        onShowBadgeDetails={onShowBadgeDetails}
        onShowPolicyDetails={onShowPolicyDetails}
        farmName={farmName}
        position={modalPosition}
        activeModal={activeModal}
        nodeData={activeNodeData}
      />

      <BadgeDetailsModal
        isOpen={activeModal === "badge"}
        onClose={onClose}
        farmName={farmName}
        position={modalPosition}
        nodeData={activeNodeData}
      />

      <PolicyDetailsModal
        isOpen={activeModal === "policy"}
        onClose={onClose}
        nodeData={activeNodeData}
        farmName={farmName}
        position={modalPosition}
      />
    </>
  )
}

export default ModalContainer
