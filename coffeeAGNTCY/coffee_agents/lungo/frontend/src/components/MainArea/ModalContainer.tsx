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
  return (
    <>
      <IdentityModal
        isOpen={activeModal === "identity"}
        onClose={onClose}
        onShowBadgeDetails={onShowBadgeDetails}
        onShowPolicyDetails={onShowPolicyDetails}
        nodeName={activeNodeData?.label1 || ""}
        position={modalPosition}
        activeModal={activeModal}
        nodeData={activeNodeData}
        isMcpServer={activeNodeData?.isMcpServer}
      />

      <BadgeDetailsModal
        isOpen={activeModal === "badge"}
        onClose={onClose}
        nodeName={activeNodeData?.label1 || ""}
        position={modalPosition}
        nodeData={activeNodeData}
        isMcpServer={activeNodeData?.isMcpServer}
      />

      <PolicyDetailsModal
        isOpen={activeModal === "policy"}
        onClose={onClose}
        nodeData={activeNodeData}
        nodeName={activeNodeData?.label1 || ""}
        position={modalPosition}
        isMcpServer={activeNodeData?.isMcpServer}
      />
    </>
  )
}

export default ModalContainer
