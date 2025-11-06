/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect } from "react"
import { createPortal } from "react-dom"

const Spinner: React.FC = () => (
  <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-solid border-node-text-primary border-r-transparent"></div>
)

interface PolicyDetailsModalProps {
  isOpen: boolean
  onClose: () => void
  farmName: string
  position: { x: number; y: number }
}

interface PolicyData {
  policyId: string
  farmName: string
  policyType: string
  effectiveDate: string
  lastUpdated: string
  version: string
  complianceStatus: string
  policies: {
    environmentalPolicy: {
      waterUsage: string
      soilConservation: string
      biodiversityProtection: string
      carbonFootprint: string
    }
    laborPolicy: {
      fairWages: boolean
      workingHours: string
      safetyStandards: string
      childLaborCompliance: boolean
    }
    qualityPolicy: {
      processingStandards: string
      storageRequirements: string
      transportationGuidelines: string
      tracingSystem: string
    }
  }
  auditTrail: {
    lastReview: string
    reviewedBy: string
    nextReviewDue: string
    complianceScore: number
  }
}

const PolicyDetailsModal: React.FC<PolicyDetailsModalProps> = ({
  isOpen,
  onClose,
  farmName,
  position,
}) => {
  const [policyData, setPolicyData] = useState<PolicyData | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isOpen) {
      fetchPolicyDetails()
    }
  }, [isOpen, farmName])

  const fetchPolicyDetails = async () => {
    setLoading(true)
    await new Promise((resolve) => setTimeout(resolve, 600))

    const mockData: PolicyData = {
      policyId: `POL-${farmName.toUpperCase()}-2024`,
      farmName: farmName,
      policyType: "Comprehensive Farm Policy",
      effectiveDate: "2024-01-01",
      lastUpdated: "2024-11-01",
      version: "2.1",
      complianceStatus: "Fully Compliant",
      policies: {
        environmentalPolicy: {
          waterUsage: "Efficient irrigation systems with 30% reduction target",
          soilConservation: "Organic composting and crop rotation implemented",
          biodiversityProtection:
            "Native species preservation zones established",
          carbonFootprint:
            "Carbon neutral operations achieved through renewable energy",
        },
        laborPolicy: {
          fairWages: true,
          workingHours: "Maximum 8 hours per day with adequate breaks",
          safetyStandards:
            "Full PPE provided and safety training conducted monthly",
          childLaborCompliance: true,
        },
        qualityPolicy: {
          processingStandards: "ISO 22000 certified processing facilities",
          storageRequirements:
            "Climate-controlled storage with humidity monitoring",
          transportationGuidelines:
            "Cold chain maintained throughout transport",
          tracingSystem: "Blockchain-based traceability from farm to cup",
        },
      },
      auditTrail: {
        lastReview: "2024-10-20",
        reviewedBy: "International Coffee Standards Authority",
        nextReviewDue: "2025-04-20",
        complianceScore: 98,
      },
    }

    setPolicyData(mockData)
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
          className="flex max-h-[30vh] w-[500px] flex-col items-start gap-4 rounded-md bg-node-background p-4 shadow-lg"
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
          ) : policyData ? (
            <div className="flex max-h-[20vh] min-h-0 w-full flex-col gap-3 overflow-y-auto">
              <h3 className="text-sm font-semibold text-node-text-primary">
                Policy Details
              </h3>
              <pre className="overflow-auto whitespace-pre-wrap rounded border bg-gray-500 bg-opacity-20 p-3 font-mono text-xs text-node-text-primary">
                {JSON.stringify(policyData, null, 2)}
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

export default PolicyDetailsModal
