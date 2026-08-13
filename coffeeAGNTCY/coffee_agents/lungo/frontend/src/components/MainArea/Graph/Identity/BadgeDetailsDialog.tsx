/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React, { useState, useEffect, useCallback } from "react"
import { Box, LoadingErrorState, Stack } from "@open-ui-kit/core"
import Dialog from "@/components/dialog/Dialog"
import { BadgeData } from "./types"
import { CustomNodeData } from "../Elements/types"
import {
  badgeDetailsEndpointLabelForReport,
  fetchBadgeDetails,
} from "./IdentityApi"
import { reportRequestError } from "@/errors/request"
import { LoadingSpinner } from "@/components/loading"
import { compactNegativeEmptyStateProps } from "@/components/compactNegativeEmptyState"
import {
  graphDialogLoadingOverlaySx,
  graphDialogPreSx,
  graphDialogScrollBodySx,
} from "../graphDialogStyles"

interface BadgeDetailsDialogProps {
  isOpen: boolean
  onClose: () => void
  nodeName: string
  nodeData: CustomNodeData
}

const BadgeDetailsDialog: React.FC<BadgeDetailsDialogProps> = ({
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
    } catch (error) {
      const httpError = reportRequestError(
        badgeDetailsEndpointLabelForReport(nodeData),
        error,
      )
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
    <Dialog open={isOpen} onClose={onClose} title={`${nodeName} Badge Details`}>
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
          <Stack sx={graphDialogScrollBodySx}>
            <Box component="pre" sx={graphDialogPreSx}>
              {JSON.stringify(badgeData, null, 2)}
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

export default BadgeDetailsDialog
