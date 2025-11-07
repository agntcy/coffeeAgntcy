/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect } from "react"
import { createPortal } from "react-dom"
import { PolicyData } from "./types"

const Spinner: React.FC = () => (
  <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-solid border-node-text-primary border-r-transparent"></div>
)

export interface PolicyDetailsModalProps {
  isOpen: boolean
  onClose: () => void
  farmName: string
  position: { x: number; y: number }
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
      policies: [
        {
          id: "fd5fca1b-77d1-4668-b121-d299eef1c736",
          name: "Invoke Vietnam",
          description: "",
          assignedTo: "6824b111-9968-4cdf-8ffc-1cfa5a108083",
          rules: [
            {
              id: "0d8acb6c-faf3-4107-a843-2c5003e3b546",
              name: "allow",
              description: "",
              tasks: [],
              action: "RULE_ACTION_ALLOW",
              needsApproval: false,
              createdAt: "2025-11-05T22:09:01.212852Z",
            },
          ],
          createdAt: "2025-11-05T22:09:00.949558Z",
        },
        {
          id: "75cc939d-178e-4a74-8d93-10829723b15e",
          name: "authenicate user",
          description: "",
          assignedTo: "6824b111-9968-4cdf-8ffc-1cfa5a108083",
          rules: [
            {
              id: "4ca7e705-4a5e-45fb-b4c9-10f3bf2a8497",
              name: "test",
              description: "",
              tasks: [],
              action: "RULE_ACTION_DENY",
              needsApproval: false,
              createdAt: "2025-11-05T19:07:10.013314Z",
            },
          ],
          createdAt: "2025-11-05T19:07:09.760338Z",
        },
      ],
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
          className="relative flex max-h-[36vh] w-[500px] flex-col items-start gap-4 rounded-md bg-node-background p-4 shadow-lg"
          onClick={handleModalClick}
          data-modal-content
        >
          {/* Close button - absolute positioned overlay */}
          <button
            onClick={onClose}
            className="absolute right-2 top-2 z-10 rounded-full bg-gray-700 bg-opacity-50 p-1 text-lg leading-none text-node-text-primary hover:bg-opacity-70"
          >
            ×
          </button>

          {loading ? (
            <div className="flex w-full items-center justify-center py-8">
              <Spinner />
            </div>
          ) : policyData ? (
            <div className="flex max-h-[26vh] min-h-0 w-full flex-col gap-3 overflow-y-auto">
              <h3 className="mb-3 text-lg font-semibold text-node-text-primary">
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
