/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect, useCallback } from "react"
import {
  Box,
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  LoadingErrorState,
  Stack,
} from "@open-ui-kit/core"
import Close from "@mui/icons-material/Close"
import { PolicyData } from "./types"
import { CustomNodeData } from "../Elements/types"
import { fetchPolicyDetails } from "./IdentityApi"
import { reportRequestError } from "@/errors/request"
import { LoadingSpinner } from "@/components/loading"
import { modalDialogContentSx } from "@/components/modalDialogContentSx"
import { compactNegativeEmptyStateProps } from "@/components/compactNegativeEmptyState"
import {
  graphModalLoadingOverlaySx,
  graphModalPreSx,
  graphModalScrollBodySx,
} from "../graphModalStyles"

export interface PolicyDetailsModalProps {
  isOpen: boolean
  onClose: () => void
  nodeName: string
  nodeData: CustomNodeData
}

const PolicyDetailsModal: React.FC<PolicyDetailsModalProps> = ({
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
    } catch (err) {
      // Modal boundary label; HTTP route is identityAppsPolicies — see urls.ts.
      const httpError = reportRequestError("identity/policy-details", err)
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
      maxWidth="md"
      fullWidth
      scroll="paper"
    >
      <DialogTitle sx={{ pr: 6, position: "relative" }}>
        {nodeName} Policy Details
        <IconButton
          onClick={onClose}
          aria-label="Close"
          sx={{ position: "absolute", right: 8, top: 8 }}
        >
          <Close />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers sx={modalDialogContentSx}>
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
            <Stack sx={graphModalScrollBodySx}>
              <Box component="pre" sx={graphModalPreSx}>
                {JSON.stringify(policyData, null, 2)}
              </Box>
              {loading ? (
                <Box sx={graphModalLoadingOverlaySx}>
                  <LoadingSpinner compact />
                </Box>
              ) : null}
            </Stack>
          ) : null}
        </LoadingErrorState>
      </DialogContent>
    </Dialog>
  )
}

export default PolicyDetailsModal
