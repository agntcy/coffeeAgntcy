/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from "react"
import { createPortal } from "react-dom"

interface IdentityModalProps {
  isOpen: boolean
  onClose: () => void
  onShowBadgeDetails: () => void
  onShowPolicyDetails: () => void
  farmName: string
  position: { x: number; y: number }
}

const IdentityModal: React.FC<IdentityModalProps> = ({
  isOpen,
  onClose,
  onShowBadgeDetails,
  onShowPolicyDetails,
  farmName,
  position,
}) => {
  console.log("IdentityModal render:", { isOpen, farmName, position })

  if (!isOpen) return null

  const handleModalClick = (e: React.MouseEvent) => {
    e.stopPropagation()
  }

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  return createPortal(
    <div className="pointer-events-none fixed inset-0 z-50">
      <div
        className="pointer-events-auto absolute inset-0 top-[60px]"
        onClick={handleBackdropClick}
      />
      <div
        className="pointer-events-auto absolute -translate-x-1/2"
        style={{
          left: `${position.x}px`,
          top: `${position.y}px`,
        }}
      >
        <div
          className="flex h-[104px] w-[240px] flex-col items-start gap-2 rounded-md bg-node-background p-2 shadow-lg"
          onClick={handleModalClick}
          data-modal-content
        >
          <div className="flex h-[88px] w-56 flex-col items-start">
            <button
              onClick={onShowBadgeDetails}
              className="flex h-11 w-56 flex-row items-center gap-3 rounded-sm px-3 transition-colors hover:bg-gray-500 hover:bg-opacity-20"
            >
              <div className="flex h-11 w-[200px] flex-grow flex-row items-center gap-1.5 py-2">
                <div className="flex h-7 w-[200px] flex-grow flex-row items-center gap-1.5">
                  <span className="h-5 w-[174px] flex-grow font-inter text-sm font-normal leading-5 text-node-text-primary">
                    Badge details
                  </span>
                </div>
              </div>
            </button>

            <button
              onClick={onShowPolicyDetails}
              className="flex h-11 w-56 flex-row items-center gap-3 rounded-sm px-3 transition-colors hover:bg-gray-500 hover:bg-opacity-20"
            >
              <div className="flex h-11 w-[200px] flex-grow flex-row items-center gap-1.5 py-2">
                <div className="flex h-7 w-[200px] flex-grow flex-row items-center gap-1.5">
                  <span className="h-5 w-[174px] flex-grow font-inter text-sm font-normal leading-5 text-node-text-primary">
                    Policy details
                  </span>
                </div>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>,
    document.body,
  )
}

export default IdentityModal
