/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { Eye, X } from "lucide-react"
import { createPortal } from "react-dom"
import { IdentityModalProps } from "./types"

const IdentityModal: React.FC<IdentityModalProps> = ({
  isOpen,
  onClose,
  onShowBadgeDetails,
  onShowPolicyDetails,
  position,
  activeModal,
}) => {
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
          className="relative flex h-[120px] w-[240px] flex-col items-start gap-2 rounded-md bg-node-background p-2 shadow-lg"
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
          <div className="mt-4 flex h-[88px] w-56 flex-col items-start">
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
          </div>
        </div>
      </div>
    </div>,
    document.body,
  )
}

export default IdentityModal
