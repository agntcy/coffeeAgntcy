/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import InfoOutlined from "@mui/icons-material/InfoOutlined"
import { Box } from "@open-ui-kit/core"
import { IconButtonDropdown } from "@/components/IconButtonDropdown"
import IdentityDetailsDropdown from "./Graph/Identity/IdentityDetailsDropdown"
import BadgeDetailsModal from "./Graph/Identity/BadgeDetailsModal"
import PolicyDetailsModal from "./Graph/Identity/PolicyDetailsModal"
import type { ModalType, ModalNodeData, ModalPosition } from "@/types/modal"
import type { CustomNodeData } from "./Graph/Elements/types"

interface ModalContainerProps {
  activeModal: ModalType
  activeNodeData: ModalNodeData
  modalPosition: ModalPosition
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
  const isMcpServer = activeNodeData?.isMcpServer

  return (
    <>
      {activeModal === "identity" && activeNodeData ? (
        <Box
          sx={{
            position: "fixed",
            left: modalPosition.x,
            top: modalPosition.y,
            zIndex: (theme) => theme.zIndex.modal,
            pointerEvents: "auto",
            ...(isMcpServer ? {} : { transform: "translateX(-50%)" }),
          }}
        >
          <IconButtonDropdown
            ariaLabel="Agent identity"
            open
            onOpenChange={(next) => {
              if (!next) onClose()
            }}
            trigger={{
              kind: "iconButton",
              icon: <InfoOutlined fontSize="small" />,
              iconButtonProps: { size: "small", color: "inherit" },
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
            <IdentityDetailsDropdown
              nodeData={activeNodeData}
              onShowBadgeDetails={onShowBadgeDetails}
              onShowPolicyDetails={onShowPolicyDetails}
            />
          </IconButtonDropdown>
        </Box>
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
