/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import InfoOutlined from "@mui/icons-material/InfoOutlined"
import { IconButtonDropdown } from "@/components/IconButtonDropdown"
import IdentityDetailsDropdownContent from "./Graph/Identity/IdentityDetailsDropdownContent"
import BadgeDetailsModal from "./Graph/Identity/BadgeDetailsModal"
import PolicyDetailsModal from "./Graph/Identity/PolicyDetailsModal"
import type { ModalType, ModalNodeData } from "@/types/modal"
import { graphSideIconButtonSx } from "./Graph/Elements/graphNodeSurface"
import type { CustomNodeData } from "./Graph/Elements/types"

interface ModalContainerProps {
  activeModal: ModalType
  activeNodeData: ModalNodeData
  onClose: () => void
  onShowBadgeDetails: () => void
  onShowPolicyDetails: () => void
}

const ModalContainer: React.FC<ModalContainerProps> = ({
  activeModal,
  activeNodeData,
  onClose,
  onShowBadgeDetails,
  onShowPolicyDetails,
}) => {
  // TODO: check identity dropdown appearance and placement
  return (
    <>
      {activeModal === "identity" && activeNodeData ? (
        <IconButtonDropdown
          ariaLabel="Agent identity"
          tooltipTitle="View agent identity details"
          open
          onOpenChange={(next) => {
            if (!next) onClose()
          }}
          trigger={{
            icon: <InfoOutlined />,
            iconButtonProps: {
              color: "inherit",
              sx: (t) => graphSideIconButtonSx(t),
            },
          }}
          closeOnContentClick={false}
          menuProps={{
            slotProps: {
              paper: {
                sx: { minWidth: 260, maxWidth: 360, padding: 0 },
              },
            },
          }}
        >
          <IdentityDetailsDropdownContent
            nodeData={activeNodeData}
            onShowBadgeDetails={onShowBadgeDetails}
            onShowPolicyDetails={onShowPolicyDetails}
          />
        </IconButtonDropdown>
      ) : null}

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
