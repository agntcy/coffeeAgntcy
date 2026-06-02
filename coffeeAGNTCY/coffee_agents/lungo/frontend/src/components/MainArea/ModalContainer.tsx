/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import BadgeDetailsModal from "./Graph/Identity/BadgeDetailsModal"
import PolicyDetailsModal from "./Graph/Identity/PolicyDetailsModal"
import type { ModalType, ModalNodeData } from "@/types/modal"
import type { CustomNodeData } from "./Graph/Elements/types"

interface ModalContainerProps {
  activeModal: ModalType
  activeNodeData: ModalNodeData
  onClose: () => void
}

const ModalContainer: React.FC<ModalContainerProps> = ({
  activeModal,
  activeNodeData,
  onClose,
}) => {
  return (
    <>
      <BadgeDetailsModal
        isOpen={activeModal === "badge"}
        onClose={onClose}
        nodeName={activeNodeData?.label1 || ""}
        nodeData={(activeNodeData ?? undefined) as CustomNodeData}
      />

      <PolicyDetailsModal
        isOpen={activeModal === "policy"}
        onClose={onClose}
        nodeData={(activeNodeData ?? undefined) as CustomNodeData}
        nodeName={activeNodeData?.label1 || ""}
      />
    </>
  )
}

export default ModalContainer
