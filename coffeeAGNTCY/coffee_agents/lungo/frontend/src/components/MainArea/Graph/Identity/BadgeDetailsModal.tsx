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
import { BadgeData } from "./types"
import { CustomNodeData } from "../Elements/types"
import { fetchBadgeDetails } from "./IdentityApi"
import { reportRequestError } from "@/errors/request"
import { LoadingSpinner } from "@/components/loading"
import { modalDialogContentSx } from "@/components/modalDialogContentSx"
import { compactNegativeEmptyStateProps } from "@/components/compactNegativeEmptyState"
import {
  graphModalLoadingOverlaySx,
  graphModalPreSx,
  graphModalScrollBodySx,
} from "../graphModalStyles"

interface BadgeDetailsModalProps {
  isOpen: boolean
  onClose: () => void
  nodeName: string
  nodeData: CustomNodeData
}

const BadgeDetailsModal: React.FC<BadgeDetailsModalProps> = ({
  isOpen,
  onClose,
  nodeName,
  nodeData,
}) => {
  const [badgeData, setBadgeData] = useState<BadgeData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchBadgeDetailsData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchBadgeDetails(nodeData)
      setBadgeData(data)
    } catch (err) {
      // Modal boundary label; HTTP route is identityAppsBadge — see urls.ts.
      const httpError = reportRequestError("identity/badge-details", err)
      setError(httpError.message)
    } finally {
      setLoading(false)
    }
  }, [nodeData])

  useEffect(() => {
    if (isOpen && nodeData) {
      fetchBadgeDetailsData()
    }
  }, [fetchBadgeDetailsData, isOpen, nodeName, nodeData])

  return (
    <Dialog
      open={isOpen}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      scroll="paper"
    >
      <DialogTitle sx={{ pr: 6, position: "relative" }}>
        {nodeName} Badge Details
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
          loading={loading && !badgeData}
          error={error !== null}
          data={error ? null : badgeData}
          skipEmptyCheck
          errorStateProps={{
            variant: "negative",
            ...compactNegativeEmptyStateProps,
            title: "Failed to load badge details",
            description: error ?? "",
            actionTitle: "Retry",
            actionCallback: () => {
              void fetchBadgeDetailsData()
            },
          }}
          emptyStateProps={{
            variant: "info",
            title: "No data available",
          }}
        >
          {badgeData ? (
            <Stack sx={graphModalScrollBodySx}>
              <Box component="pre" sx={graphModalPreSx}>
                {JSON.stringify(badgeData, null, 2)}
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

export default BadgeDetailsModal
