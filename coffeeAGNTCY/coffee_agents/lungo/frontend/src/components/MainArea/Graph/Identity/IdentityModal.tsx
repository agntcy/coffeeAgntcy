/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Eye } from "lucide-react"
import { createPortal } from "react-dom"
import { IdentityModalProps } from "./types"
import { useThemeIcon } from "@/hooks/useThemeIcon"
import { useEscapeKey } from "@/hooks/useEscapeKey"
import githubIcon from "@/assets/Github.png"
import githubIconLight from "@/assets/Github_lightmode.png"
import urlsConfig from "@/utils/urls.json"

const IdentityModal: React.FC<IdentityModalProps> = ({
  isOpen,
  onClose,
  onShowBadgeDetails,
  onShowPolicyDetails,
  position,
  activeModal,
  nodeData,
  isMcpServer,
}) => {
  const githubIconSrc = useThemeIcon({
    light: githubIconLight,
    dark: githubIcon,
  })

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
          <button
            onClick={onClose}
            className="absolute right-3 top-3 z-10 text-xl leading-none text-node-text-secondary transition-colors hover:text-node-text-primary"
          >
            ×
          </button>

          <h3 className="mb-3 text-lg font-semibold text-node-text-primary">
            Agent Identity Details
          </h3>

          <div className="flex w-full flex-col gap-1 overflow-y-auto rounded border border-gray-600 p-3">
            {nodeData?.hasBadgeDetails && (
              <button
                onClick={onShowBadgeDetails}
                className={`flex h-11 w-full items-center justify-between gap-3 rounded-sm px-3 transition-colors hover:bg-gray-500 hover:bg-opacity-20 ${
                  activeModal === "badge"
                    ? "border border-accent-border bg-accent-border bg-opacity-20"
                    : ""
                }`}
              >
                <span className="text-left font-inter text-sm font-normal leading-5 text-node-text-primary">
                  Badge details
                </span>
                <Eye className="h-4 w-4 text-node-text-secondary" />
              </button>
            )}

            {nodeData?.hasPolicyDetails && (
              <button
                onClick={onShowPolicyDetails}
                className={`flex h-11 w-full items-center justify-between gap-3 rounded-sm px-3 transition-colors hover:bg-gray-500 hover:bg-opacity-20 ${
                  activeModal === "policy"
                    ? "border border-accent-border bg-accent-border bg-opacity-20"
                    : ""
                }`}
              >
                <span className="text-left font-inter text-sm font-normal leading-5 text-node-text-primary">
                  Policy details
                </span>
                <Eye className="h-4 w-4 text-node-text-secondary" />
              </button>
            )}

            {identityGithubUrl && (
              <button
                onClick={() =>
                  window.open(
                    identityGithubUrl,
                    "_blank",
                    "noopener,noreferrer",
                  )
                }
                className="flex h-11 w-full items-center justify-between gap-3 rounded-sm px-3 transition-colors hover:bg-gray-500 hover:bg-opacity-20"
              >
                <span className="text-left font-inter text-sm font-normal leading-5 text-node-text-primary">
                  Source code
                </span>
                <img src={githubIconSrc} alt="GitHub" className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>,
    document.body,
  )
}

export default IdentityModal
