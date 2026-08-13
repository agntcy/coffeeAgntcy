/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect, useCallback } from "react"
import { Box, LoadingErrorState, Stack } from "@open-ui-kit/core"
import Dialog from "@/components/dialog/Dialog"
import { PolicyData } from "./types"
import { CustomNodeData } from "../Elements/types"
import {
  fetchPolicyDetails,
  policyDetailsEndpointLabelForReport,
} from "./IdentityApi"
import { reportRequestError } from "@/errors/request"
import { LoadingSpinner } from "@/components/loading"
import { compactNegativeEmptyStateProps } from "@/components/compactNegativeEmptyState"
import {
  graphDialogLoadingOverlaySx,
  graphDialogPreSx,
  graphDialogScrollBodySx,
} from "../graphDialogStyles"

export interface PolicyDetailsDialogProps {
  isOpen: boolean
  onClose: () => void
  nodeName: string
  nodeData: CustomNodeData
}

const PolicyDetailsDialog: React.FC<PolicyDetailsDialogProps> = ({
  isOpen,
  onClose,
  nodeName,
  nodeData,
}) => {
  const [policyData, setPolicyData] = useState<PolicyData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchPolicyDetailsData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchPolicyDetails(nodeData)
      setPolicyData(data)
    } catch (error) {
      const httpError = reportRequestError(
        policyDetailsEndpointLabelForReport(nodeData),
        error,
      )
      setError(httpError.message)
    } finally {
      setLoading(false)
    }
  }, [nodeData])

  useEffect(() => {
    if (isOpen && nodeData) {
      fetchPolicyDetailsData()
    }
  }, [fetchPolicyDetailsData, isOpen, nodeName, nodeData])

  return (
    <Dialog
      open={isOpen}
      onClose={onClose}
      title={`${nodeName} Policy Details`}
    >
      <LoadingErrorState
        loading={loading && !policyData}
        error={error !== null}
        data={error ? null : policyData}
        skipEmptyCheck
        errorStateProps={{
          variant: "negative",
          ...compactNegativeEmptyStateProps,
          title: "Failed to load policy details",
          description: error ?? "",
          actionTitle: "Retry",
          actionCallback: () => {
            void fetchPolicyDetailsData()
          },
        }}
        emptyStateProps={{
          variant: "info",
          title: "No data available",
        }}
      >
        {policyData ? (
          <Stack sx={graphDialogScrollBodySx}>
            <Box component="pre" sx={graphDialogPreSx}>
              {JSON.stringify(policyData, null, 2)}
            </Box>
            {loading ? (
              <Box sx={graphDialogLoadingOverlaySx}>
                <LoadingSpinner compact />
              </Box>
            ) : null}
          </Stack>
        ) : null}
      </LoadingErrorState>
    </Dialog>
  )
}

export default PolicyDetailsDialog
