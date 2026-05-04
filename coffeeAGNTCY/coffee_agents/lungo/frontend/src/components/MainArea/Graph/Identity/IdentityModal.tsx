/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { IconButton } from "@open-ui-kit/core"
import Close from "@mui/icons-material/Close"
import Visibility from "@mui/icons-material/Visibility"
import Box from "@mui/material/Box"
import { createPortal } from "react-dom"
import { IdentityModalProps } from "./types"
import { useEscapeKey } from "@/hooks/useEscapeKey"
import githubIconLight from "@/assets/Github_lightmode.png"
import urlsConfig from "@/utils/urls.json"
import { SecurityClass } from "@/utils/SecurityClass"

const IdentityModal: React.FC<IdentityModalProps> = ({
  isOpen,
  onClose,
  onShowBadgeDetails,
  onShowPolicyDetails,
  position,
  nodeData,
  isMcpServer,
}) => {
  const githubIconSrc = githubIconLight

  const getIdentityGithubUrl = () => {
    if (!nodeData) return null

    const nodeName = nodeData.label1 || ""

    if (
      nodeName.toLowerCase().includes("colombia") ||
      nodeName.toLowerCase().includes("vietnam")
    ) {
      return urlsConfig.identity.colombia
    }

    if (nodeName.toLowerCase().includes("auction")) {
      return urlsConfig.identity.auction
    }

    if (nodeData.label2?.toLowerCase().includes("payment")) {
      return urlsConfig.identity.payment
    }

    return nodeData.githubLink
  }

  const identityGithubUrl = getIdentityGithubUrl()

  useEscapeKey(isOpen, onClose)

  if (!isOpen) return null

  const handleModalClick = (e: React.MouseEvent) => {
    e.stopPropagation()
  }

  return createPortal(
    <div className="pointer-events-none fixed inset-0 z-50">
      <div
        className={`pointer-events-auto absolute ${isMcpServer ? "" : "-translate-x-1/2"}`}
        style={{
          left: `${position.x}px`,
          top: `${position.y}px`,
        }}
      >
        <div
          className="relative flex h-[200px] w-[280px] flex-col items-start gap-4 rounded-md bg-node-background p-4 shadow-lg"
          onClick={handleModalClick}
          data-modal-content
        >
          <IconButton
            onClick={onClose}
            aria-label="Close"
            size="small"
            sx={{
              position: "absolute",
              right: 12,
              top: 12,
              zIndex: 10,
            }}
          >
            <Close />
          </IconButton>

          <h3 className="mb-3 text-lg font-semibold text-node-text-primary">
            Agent Identity Details
          </h3>

          <div className="flex w-full flex-col gap-1 overflow-y-auto rounded border border-gray-600 p-3">
            {nodeData?.hasBadgeDetails && (
              <IconButton
                onClick={onShowBadgeDetails}
                sx={{
                  justifyContent: "space-between",
                  gap: 1.5,
                }}
              >
                <span className="text-left font-inter text-sm font-normal leading-5">
                  Badge details
                </span>
                <Visibility />
              </IconButton>
            )}

            {nodeData?.hasPolicyDetails && (
              <IconButton
                onClick={onShowPolicyDetails}
                sx={{
                  justifyContent: "space-between",
                  gap: 1.5,
                }}
              >
                <span className="text-left font-inter text-sm font-normal leading-5">
                  Policy details
                </span>
                <Visibility />
              </IconButton>
            )}

            {identityGithubUrl &&
              SecurityClass.isSafeExternalUrl(identityGithubUrl) && (
                <IconButton
                  onClick={() =>
                    window.open(
                      identityGithubUrl,
                      "_blank",
                      "noopener,noreferrer",
                    )
                  }
                  sx={{
                    justifyContent: "space-between",
                    gap: 1.5,
                  }}
                >
                  <span className="text-left font-inter text-sm font-normal leading-5">
                    Source code
                  </span>
                  <Box
                    component="img"
                    src={githubIconSrc}
                    alt="Source code"
                    sx={{
                      bgcolor: "#ffffff",
                    }}
                  />
                </IconButton>
              )}
          </div>
        </div>
      </div>
    </div>,
    document.body,
  )
}

export default IdentityModal
