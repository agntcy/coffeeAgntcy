/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Eye, X } from "lucide-react"
import { createPortal } from "react-dom"
import { IdentityModalProps } from "./types"
import { useThemeIcon } from "@/hooks/useThemeIcon"
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
}) => {
  const githubIconSrc = useThemeIcon({
    light: githubIconLight,
    dark: githubIcon,
  })

  const getIdentityGithubUrl = () => {
    if (!nodeData) return null

    const nodeName = nodeData.label1 || ""

    if (nodeName.toLowerCase().includes("colombia")) {
      return urlsConfig.identity.colombia
    }

    if (nodeName.toLowerCase().includes("auction")) {
      return urlsConfig.identity.auction
    }

    return nodeData.githubLink
  }

  const identityGithubUrl = getIdentityGithubUrl()

  if (!isOpen) return null

  const handleModalClick = (e: React.MouseEvent) => {
    e.stopPropagation()
  }

  return createPortal(
    <div className="pointer-events-none fixed inset-0 z-50">
      <div
        className="pointer-events-auto absolute -translate-x-1/2"
        style={{
          left: `${position.x}px`,
          top: `${position.y}px`,
        }}
      >
        <div
          className="relative flex h-[160px] w-[240px] flex-col items-start gap-2 rounded-md bg-node-background p-2 shadow-lg"
          onClick={handleModalClick}
          data-modal-content
        >
          <button
            aria-label="Close identity modal"
            onClick={(e) => {
              e.stopPropagation()
              onClose()
            }}
            className="absolute right-1 top-1 flex h-5 w-5 items-center justify-center rounded-sm hover:bg-gray-500 hover:bg-opacity-10"
          >
            <X className="h-3 w-3 text-node-text-secondary" />
          </button>
          <div className="mt-4 flex h-[128px] w-56 flex-col items-start">
            <button
              onClick={onShowBadgeDetails}
              className={`flex h-11 w-56 items-center justify-between gap-3 rounded-sm px-3 transition-colors hover:bg-gray-500 hover:bg-opacity-20 ${
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

            <button
              onClick={onShowPolicyDetails}
              className={`flex h-11 w-56 items-center justify-between gap-3 rounded-sm px-3 transition-colors hover:bg-gray-500 hover:bg-opacity-20 ${
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

            {identityGithubUrl && (
              <div className="mt-2 flex w-56 justify-center">
                <a
                  href={identityGithubUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="no-underline"
                >
                  <div
                    className="flex h-7 w-7 cursor-pointer items-center justify-center rounded-lg border border-solid p-1 opacity-100 shadow-sm transition-opacity duration-200 ease-in-out"
                    style={{
                      backgroundColor: "var(--custom-node-background)",
                      borderColor: "var(--custom-node-border)",
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.opacity = "0.8"
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.opacity = "1"
                    }}
                  >
                    <img src={githubIconSrc} alt="GitHub" className="h-5 w-5" />
                  </div>
                </a>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>,
    document.body,
  )
}

export default IdentityModal
