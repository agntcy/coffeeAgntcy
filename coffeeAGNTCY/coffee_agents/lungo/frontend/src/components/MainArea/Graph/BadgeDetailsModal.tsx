/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect } from "react"
import { createPortal } from "react-dom"

interface BadgeDetailsModalProps {
  isOpen: boolean
  onClose: () => void
  farmName: string
  position: { x: number; y: number }
}

interface BadgeData {
  badgeId: string
  farmName: string
  certificationLevel: string
  issueDate: string
  expiryDate: string
  sustainabilityScore: number
  fairTradeStatus: boolean
  organicCertified: boolean
  verificationDetails: {
    verifiedBy: string
    lastAuditDate: string
    nextAuditDue: string
    complianceScore: number
  }
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
    // Mock API call - replace with actual API when ready
    await new Promise((resolve) => setTimeout(resolve, 500)) // Simulate network delay

    const mockData: BadgeData = {
      badgeId: `BADGE-${farmName.toUpperCase()}-2024`,
      farmName: farmName,
      certificationLevel: "Premium",
      issueDate: "2024-01-15",
      expiryDate: "2025-01-15",
      sustainabilityScore: 94,
      fairTradeStatus: true,
      organicCertified: farmName === "Colombia" ? true : false,
      verificationDetails: {
        verifiedBy: "Global Coffee Certification Board",
        lastAuditDate: "2024-10-15",
        nextAuditDue: "2025-04-15",
        complianceScore: 96,
      },
    }

    setBadgeData(mockData)
    setLoading(false)
  }

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
          className="flex max-h-[500px] w-[400px] flex-col items-start gap-4 overflow-y-auto rounded-md bg-node-background p-4 shadow-lg"
          onClick={handleModalClick}
          data-modal-content
        >
          <div className="flex w-full flex-row items-center justify-between">
            <h2 className="text-lg font-semibold text-node-text-primary">
              Badge Details
            </h2>
            <button
              onClick={onClose}
              className="text-xl leading-none text-node-text-primary hover:text-opacity-70"
            >
              ×
            </button>
          </div>

          {loading ? (
            <div className="flex w-full items-center justify-center py-8">
              <div className="text-node-text-primary">Loading...</div>
            </div>
          ) : badgeData ? (
            <div className="flex w-full flex-col gap-3">
              <pre className="overflow-x-auto whitespace-pre-wrap rounded border bg-gray-500 bg-opacity-20 p-3 font-mono text-xs text-node-text-primary">
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
