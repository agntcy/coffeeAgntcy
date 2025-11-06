/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect } from "react"
import { createPortal } from "react-dom"

const Spinner: React.FC = () => (
  <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-solid border-node-text-primary border-r-transparent"></div>
)

interface BadgeDetailsModalProps {
  isOpen: boolean
  onClose: () => void
  farmName: string
  position: { x: number; y: number }
}

interface BadgeData {
  id: string
  farmName: string
  verified: boolean
  policies: number
}

const BadgeDetailsModal: React.FC<BadgeDetailsModalProps> = ({
  isOpen,
  onClose,
  farmName,
  position,
}) => {
  const [badgeData, setBadgeData] = useState<BadgeData | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isOpen) {
      fetchBadgeDetails()
    }
  }, [isOpen, farmName])

  const fetchBadgeDetails = async () => {
    setLoading(true)
    await new Promise((resolve) => setTimeout(resolve, 500))

    const mockData: BadgeData = {
      id: `BADGE-${farmName.toUpperCase()}-2024`,
      farmName: farmName,
      verified: true,
      policies: 3,
    }

    setBadgeData(mockData)
    setLoading(false)
  }

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
          className="flex max-h-[30vh] w-[400px] flex-col items-start gap-4 rounded-md bg-node-background p-4 shadow-lg"
          onClick={handleModalClick}
          data-modal-content
        >
          <div className="flex w-full flex-shrink-0 flex-row items-center justify-end">
            <button
              onClick={onClose}
              className="text-xl leading-none text-node-text-primary hover:text-opacity-70"
            >
              ×
            </button>
          </div>

          {loading ? (
            <div className="flex w-full items-center justify-center py-8">
              <Spinner />
            </div>
          ) : badgeData ? (
            <div className="flex max-h-[20vh] min-h-0 w-full flex-col gap-3 overflow-y-auto">
              <h3 className="text-sm font-semibold text-node-text-primary">
                {farmName} Badge Details
              </h3>
              <pre className="overflow-auto whitespace-pre-wrap rounded border bg-gray-500 bg-opacity-20 p-3 font-mono text-xs text-node-text-primary">
                {JSON.stringify(badgeData, null, 2)}
              </pre>
            </div>
          ) : (
            <div className="flex w-full items-center justify-center py-8">
              <div className="text-node-text-primary">No data available</div>
            </div>
          )}
        </div>
      </div>
    </div>,
    document.body,
  )
}

export default BadgeDetailsModal
